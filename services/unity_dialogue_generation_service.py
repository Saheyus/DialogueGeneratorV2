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
        
        # Valider et limiter le nombre de choix si max_choices est spécifié
        if max_choices is not None:
            for node in result.nodes:
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
        
        logger.info(f"Nœud généré avec succès: {len(result.nodes)} nœud(s)")
        return result
    
    def enrich_with_ids(
        self,
        content: UnityDialogueGenerationResponse,
        start_id: str = "START"
    ) -> List[Dict[str, Any]]:
        """Ajoute les IDs techniques et gère la navigation.
        
        Pour chaque nœud :
        1. Génère un ID unique (START pour le premier, puis NODE_1, NODE_2...)
        2. Résout les références (successNode, failureNode, targetNode) en utilisant
           des IDs relatifs ou en créant des IDs pour les nœuds référencés
        3. Ajoute nextNode si manquant et pas de choix (navigation linéaire)
        4. Convertit en dict pour UnityJsonRenderer
        
        Args:
            content: Réponse de génération contenant les nœuds sans IDs.
            start_id: ID à utiliser pour le premier nœud (par défaut "START").
            
        Returns:
            Liste de dictionnaires représentant les nœuds Unity avec IDs.
        """
        logger.info(f"Enrichissement de {len(content.nodes)} nœud(s) avec IDs techniques")
        
        enriched_nodes: List[Dict[str, Any]] = []
        node_index = 0
        
        # Créer un mapping des indices vers les IDs générés
        # Pour l'instant, on génère un nœud à la fois, donc on n'a qu'un seul nœud
        # Mais on prépare la structure pour l'extension future
        
        for node_content in content.nodes:
            # Générer l'ID
            if node_index == 0:
                node_id = start_id
            else:
                node_id = f"NODE_{node_index}"
            
            # Convertir le nœud en dict
            node_dict: Dict[str, Any] = {
                "id": node_id
            }
            
            # Ajouter les champs du contenu
            if node_content.speaker:
                node_dict["speaker"] = node_content.speaker
            if node_content.line:
                node_dict["line"] = node_content.line
            if node_content.test:
                node_dict["test"] = node_content.test
            if node_content.successNode:
                # Pour l'instant, on garde la référence telle quelle
                # Le système de validation signalera si elle est invalide
                node_dict["successNode"] = node_content.successNode
            if node_content.failureNode:
                node_dict["failureNode"] = node_content.failureNode
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
                        "text": choice_content.text
                    }
                    
                    # targetNode est requis dans le format Unity, même s'il est vide
                    if choice_content.targetNode:
                        choice_dict["targetNode"] = choice_content.targetNode
                    else:
                        choice_dict["targetNode"] = ""  # Vide mais présent pour validation
                    
                    # Ajouter les champs optionnels du choix
                    if choice_content.test:
                        choice_dict["test"] = choice_content.test
                    if choice_content.testSuccessNode:
                        choice_dict["testSuccessNode"] = choice_content.testSuccessNode
                    if choice_content.testFailureNode:
                        choice_dict["testFailureNode"] = choice_content.testFailureNode
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
            
            # Gérer nextNode
            # Si pas de choix et pas de nextNode, on ne l'ajoute pas (le dialogue se termine)
            # Si nextNode est fourni, on l'ajoute
            if not node_content.choices and node_content.nextNode:
                node_dict["nextNode"] = node_content.nextNode
            
            enriched_nodes.append(node_dict)
            node_index += 1
        
        logger.info(f"Enrichissement terminé: {len(enriched_nodes)} nœud(s) avec IDs")
        return enriched_nodes

