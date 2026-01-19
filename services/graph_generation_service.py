"""Service pour générer des nœuds de dialogue en batch pour tous les choix d'un nœud parent."""
import logging
from typing import List, Dict, Any, Optional

from services.unity_dialogue_generation_service import UnityDialogueGenerationService
from core.llm.llm_client import ILLMClient

logger = logging.getLogger(__name__)


class GraphGenerationService:
    """Service pour générer des nœuds de dialogue en batch.
    
    Génère un nœud pour chaque choix d'un nœud parent qui n'a pas encore de targetNode.
    Gère automatiquement les IDs et les connexions.
    """
    
    def __init__(self, generation_service: Optional[UnityDialogueGenerationService] = None):
        """Initialise le service.
        
        Args:
            generation_service: Service de génération Unity (par défaut: nouvelle instance).
        """
        self.generation_service = generation_service or UnityDialogueGenerationService()
        logger.info("GraphGenerationService initialisé")
    
    async def generate_nodes_for_all_choices(
        self,
        parent_node: Dict[str, Any],
        instructions: str,
        context: Dict[str, Any],
        llm_client: ILLMClient,
        system_prompt_override: Optional[str] = None,
        max_choices: Optional[int] = None
    ) -> Dict[str, Any]:
        """Génère un nœud pour chaque choix du parent sans targetNode.
        
        Args:
            parent_node: Nœud parent avec choix (format Unity JSON).
            instructions: Instructions pour guider la génération.
            context: Contexte GDD (non utilisé directement ici, mais peut être passé au prompt).
            llm_client: Client LLM pour la génération.
            system_prompt_override: Surcharge du system prompt (optionnel).
            max_choices: Nombre maximum de choix pour chaque nœud généré (optionnel).
            
        Returns:
            Dictionnaire avec:
            - "nodes": Liste de nœuds générés (avec IDs)
            - "connections": Liste de connexions suggérées (format SuggestedConnection)
        """
        parent_id = parent_node.get("id", "UNKNOWN")
        parent_choices = parent_node.get("choices", [])
        
        # Filtrer les choix sans targetNode (ou avec "END")
        choices_to_generate = []
        for i, choice in enumerate(parent_choices):
            target_node = choice.get("targetNode")
            if not target_node or target_node == "END":
                choices_to_generate.append((i, choice))
        
        if not choices_to_generate:
            logger.info(f"Aucun choix à générer pour le nœud parent {parent_id} (tous déjà connectés)")
            return {"nodes": [], "connections": []}
        
        logger.info(
            f"Génération batch: {len(choices_to_generate)} nœud(s) pour le parent {parent_id}"
        )
        
        generated_nodes = []
        suggested_connections = []
        failed_choices = []  # Tracker les choix qui ont échoué
        
        # Générer un nœud pour chaque choix filtré
        for choice_index, choice in choices_to_generate:
            choice_text = choice.get("text", "")
            parent_speaker = parent_node.get("speaker", "PNJ")
            parent_line = parent_node.get("line", "")
            
            # Construire le prompt enrichi avec le contexte du choix
            enriched_instructions = f"""Contexte précédent:
{parent_speaker}: {parent_line}

Réponse du joueur:
{choice_text}

Instructions pour la suite:
{instructions}
"""
            
            # Générer le nœud
            try:
                response = await self.generation_service.generate_dialogue_node(
                    llm_client=llm_client,
                    prompt=enriched_instructions,
                    system_prompt_override=system_prompt_override,
                    max_choices=max_choices
                )
                
                # Enrichir avec ID au format NODE_{parent_id}_CHOICE_{index}
                # parent_id peut déjà contenir "NODE_" ou non, on l'utilise tel quel
                if parent_id.startswith("NODE_"):
                    # parent_id est déjà au format "NODE_XXX", on l'utilise directement
                    start_id = f"{parent_id}_CHOICE_{choice_index}"
                else:
                    # parent_id est juste "XXX", on ajoute le préfixe
                    start_id = f"NODE_{parent_id}_CHOICE_{choice_index}"
                enriched_nodes = self.generation_service.enrich_with_ids(
                    content=response,
                    start_id=start_id
                )
                
                if enriched_nodes:
                    generated_node = enriched_nodes[0]
                    # Valider que le nœud a un ID avant de l'ajouter
                    if not generated_node.get("id"):
                        logger.error(
                            f"Nœud généré pour choix {choice_index} n'a pas d'ID - ignoré"
                        )
                        continue
                    
                    generated_nodes.append(generated_node)
                    
                    # Créer la connexion suggérée
                    suggested_connections.append({
                        "from": parent_id,
                        "to": generated_node["id"],
                        "via_choice_index": choice_index,
                        "connection_type": "choice"
                    })
                    
                    logger.debug(
                        f"Nœud généré pour choix {choice_index}: {generated_node['id']}"
                    )
                else:
                    logger.warning(
                        f"Aucun nœud enrichi retourné pour choix {choice_index} du parent {parent_id}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Erreur lors de la génération du nœud pour choix {choice_index} "
                    f"du parent {parent_id}: {e}",
                    exc_info=True
                )
                # Tracker l'échec pour rapport
                failed_choices.append({
                    "choice_index": choice_index,
                    "choice_text": choice.get("text", ""),
                    "error": str(e)
                })
                # Continuer avec les autres choix même si un échoue
                continue
        
        # Logger un avertissement si des échecs partiels
        if failed_choices:
            logger.warning(
                f"Génération batch partielle: {len(generated_nodes)}/{len(choices_to_generate)} "
                f"nœud(s) généré(s) avec succès, {len(failed_choices)} échec(s) pour le parent {parent_id}"
            )
        else:
            logger.info(
                f"Génération batch terminée: {len(generated_nodes)} nœud(s) généré(s) "
                f"pour le parent {parent_id}"
            )
        
        return {
            "nodes": generated_nodes,
            "connections": suggested_connections,
            "failed_choices": failed_choices  # Retourner les échecs pour information
        }
