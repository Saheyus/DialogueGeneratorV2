"""Service pour générer des dialogues au format Unity JSON."""
import logging
from typing import List, Dict, Any, Optional

from models.dialogue_structure.unity_dialogue_node import (
    UnityDialogueGenerationResponse,
    UnityDialogueNodeContent,
    UnityDialogueChoiceContent
)
from llm_client import ILLMClient

logger = logging.getLogger(__name__)


class UnityDialogueGenerationService:
    """Service pour générer des dialogues au format Unity JSON.
    
    Utilise Structured Output pour que l'IA génère uniquement le contenu créatif,
    puis enrichit automatiquement avec les IDs techniques et la navigation.
    """
    
    def __init__(self):
        """Initialise le service."""
        logger.info("UnityDialogueGenerationService initialisé")
    
    async def generate_dialogue_node(
        self,
        llm_client: ILLMClient,
        prompt: str,
        system_prompt_override: Optional[str] = None,
        max_choices: Optional[int] = None
    ) -> UnityDialogueGenerationResponse:
        """Génère un nœud de dialogue via Structured Output.
        
        Args:
            llm_client: Client LLM pour la génération.
            prompt: Prompt utilisateur pour la génération.
            system_prompt_override: Surcharge du system prompt (optionnel).
            max_choices: Nombre maximum de choix à générer (0-8, ou None pour laisser l'IA décider).
            
        Returns:
            Réponse contenant les nœuds générés par l'IA (sans IDs techniques).
        """
        logger.info("Génération d'un nœud de dialogue Unity via Structured Output")
        
        # Utiliser Structured Output avec le modèle UnityDialogueGenerationResponse
        variants = await llm_client.generate_variants(
            prompt=prompt,
            k=1,
            response_model=UnityDialogueGenerationResponse,
            user_system_prompt_override=system_prompt_override
        )
        
        if not variants or len(variants) == 0:
            raise ValueError("Aucune variante générée par le LLM")
        
        result = variants[0]
        
        # Gérer le cas où DummyLLMClient retourne un dict au lieu d'un modèle Pydantic
        if isinstance(result, dict):
            logger.warning("DummyLLMClient a retourné un dict, conversion en UnityDialogueGenerationResponse")
            try:
                result = UnityDialogueGenerationResponse.model_validate(result)
            except Exception as e:
                logger.error(f"Erreur lors de la conversion du dict en UnityDialogueGenerationResponse: {e}")
                raise ValueError(f"Impossible de convertir le résultat en UnityDialogueGenerationResponse: {e}")
        
        if not isinstance(result, UnityDialogueGenerationResponse):
            raise ValueError(f"Type de réponse inattendu: {type(result)}. Attendu: UnityDialogueGenerationResponse")
        
        # Validation : vérifier que le nœud a du contenu
        node = result.node
        if not node.choices and not node.line:
            logger.warning(
                "Le nœud généré n'a ni choices ni line. "
                "Le dialogue se terminera à ce nœud."
            )
        
        # Valider et limiter le nombre de choix si max_choices est spécifié
        if max_choices is not None:
            if node.choices:
                if max_choices == 0:
                    logger.warning(
                        f"max_choices=0 mais le nœud a {len(node.choices)} choix. "
                        "Suppression des choix."
                    )
                    node.choices = None
                elif len(node.choices) > max_choices:
                    logger.warning(
                        f"Le nœud a {len(node.choices)} choix, mais max_choices={max_choices}. "
                        f"Troncature à {max_choices} choix."
                    )
                    node.choices = node.choices[:max_choices]
        else:
            # Quand max_choices est None (libre), valider que le nœud a entre 2 et 8 choix
            # Note: Si node.choices est None, c'est un nœud de fin valide (pas de validation)
            # Si node.choices est une liste (vide ou avec éléments), on valide
            if node.choices is not None:
                num_choices = len(node.choices)
                if num_choices == 0:
                    logger.error(
                        "max_choices est libre (None) mais le nœud a une liste vide de choix. "
                        "Quand max_choices est libre, le nœud doit avoir entre 2 et 8 choix, "
                        "ou None pour un nœud de fin."
                    )
                    raise ValueError(
                        "Quand 'Nombre max de choix' est vide (libre), le nœud doit avoir entre 2 et 8 choix, "
                        "mais le nœud généré a une liste vide de choix."
                    )
                elif num_choices == 1:
                    logger.error(
                        "max_choices est libre (None) mais le nœud a seulement 1 choix. "
                        "Quand max_choices est libre, le nœud doit avoir entre 2 et 8 choix."
                    )
                    raise ValueError(
                        "Quand 'Nombre max de choix' est vide (libre), le nœud doit avoir entre 2 et 8 choix, "
                        f"mais le nœud généré a seulement {num_choices} choix."
                    )
                elif num_choices > 8:
                    logger.warning(
                        f"max_choices est libre (None) mais le nœud a {num_choices} choix (> 8). "
                        "Troncature à 8 choix."
                    )
                    node.choices = node.choices[:8]
        
        logger.info("Nœud généré avec succès")
        return result
    
    def enrich_with_ids(
        self,
        content: UnityDialogueGenerationResponse,
        start_id: str = "START"
    ) -> List[Dict[str, Any]]:
        """Ajoute les IDs techniques et gère la navigation.
        
        Pour le nœud unique :
        1. Génère un ID unique (START par défaut)
        2. Ajoute targetNode: "END" pour chaque choix (champ technique géré par l'application)
        3. Convertit en dict pour UnityJsonRenderer
        
        Note: Les champs techniques (targetNode, nextNode, successNode, etc.) ne sont jamais
        générés par l'IA. Ils sont gérés uniquement par l'application.
        
        IMPORTANT - "END" comme marqueur de fin (pas un vrai nœud) :
        Le nœud "END" est utilisé par défaut comme placeholder temporaire car on génère
        un fragment de dialogue sans savoir ce qui suivra. C'est un artifice temporaire
        pour que le JSON soit valide. Si on génère la suite du dialogue plus tard,
        les targetNode seront mis à jour pour pointer vers les vrais nœuds suivants.
        
        Le nœud "END" peut aussi être la fin définitive si c'est vraiment une scène d'au revoir,
        mais ce n'est pas le problème du logiciel - c'est l'auteur qui décide.
        
        Le nœud "END" est reconnu par Unity comme marqueur de fin spécial. Il n'est PAS créé
        comme nœud explicite dans le JSON car Unity le gère implicitement. Le validateur
        accepte "END" comme référence valide même sans nœud explicite, et l'interface
        d'édition filtre "END" de l'affichage car ce n'est pas un vrai nœud éditable.
        
        Args:
            content: Réponse de génération contenant un nœud sans ID.
            start_id: ID à utiliser pour le nœud (par défaut "START").
            
        Returns:
            Liste avec un seul dictionnaire représentant le nœud Unity avec ID :
            - [START] (END n'est pas créé car Unity le gère implicitement)
        """
        logger.info("Enrichissement du nœud avec ID technique")
        
        node_content = content.node
        
        # Convertir le nœud en dict
        node_dict: Dict[str, Any] = {
            "id": start_id
        }
        
        # Ajouter les champs du contenu
        if node_content.speaker:
            node_dict["speaker"] = node_content.speaker
        if node_content.line:
            node_dict["line"] = node_content.line
        if node_content.test:
            node_dict["test"] = node_content.test
        if node_content.consequences:
            node_dict["consequences"] = {
                "flag": node_content.consequences.flag
            }
            if node_content.consequences.description:
                node_dict["consequences"]["description"] = node_content.consequences.description
        if node_content.isLongRest is not None:
            node_dict["isLongRest"] = node_content.isLongRest
        if node_content.startState is not None:
            node_dict["startState"] = node_content.startState
        
        # Gérer les choix
        if node_content.choices:
            choices_list = []
            for choice_content in node_content.choices:
                choice_dict: Dict[str, Any] = {
                    "text": choice_content.text,
                    "targetNode": "END"  # Placeholder temporaire : sera mis à jour si on génère la suite
                }
                
                # Ajouter les champs optionnels du choix (champs créatifs que l'IA peut générer)
                if choice_content.test:
                    choice_dict["test"] = choice_content.test
                if choice_content.traitRequirements:
                    choice_dict["traitRequirements"] = choice_content.traitRequirements
                if choice_content.allowInfluenceForcing is not None:
                    choice_dict["allowInfluenceForcing"] = choice_content.allowInfluenceForcing
                if choice_content.influenceThreshold is not None:
                    choice_dict["influenceThreshold"] = choice_content.influenceThreshold
                if choice_content.influenceDelta is not None:
                    choice_dict["influenceDelta"] = choice_content.influenceDelta
                if choice_content.respectDelta is not None:
                    choice_dict["respectDelta"] = choice_content.respectDelta
                if choice_content.condition:
                    choice_dict["condition"] = choice_content.condition
                
                choices_list.append(choice_dict)
            
            node_dict["choices"] = choices_list
        
        # Note: nextNode, successNode, failureNode, testSuccessNode, testFailureNode
        # sont des champs techniques qui ne doivent pas être générés par l'IA
        # Ils seront gérés par l'application si nécessaire
        
        # Ne pas créer de nœud "END" explicite : Unity gère "END" implicitement comme marqueur de fin.
        # Le validateur accepte "END" comme référence valide même sans nœud explicite.
        # Cela évite d'afficher un nœud "END" éditable dans l'interface, car ce n'est pas un vrai nœud.
        logger.info("Enrichissement terminé: nœud avec ID")
        return [node_dict]

