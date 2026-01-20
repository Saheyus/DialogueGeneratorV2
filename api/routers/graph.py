"""Router API pour la gestion de graphes de dialogues."""
import json
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status
from api.schemas.graph import (
    LoadGraphRequest,
    LoadGraphResponse,
    GraphMetadata,
    SaveGraphRequest,
    SaveGraphResponse,
    GenerateNodeRequest,
    GenerateNodeResponse,
    SuggestedConnection,
    ValidateGraphRequest,
    ValidateGraphResponse,
    ValidationErrorDetail,
    CalculateLayoutRequest,
    CalculateLayoutResponse
)
from api.exceptions import InternalServerException, ValidationException
from api.dependencies import get_request_id
from services.graph_conversion_service import GraphConversionService
from services.graph_validation_service import GraphValidationService
from services.unity_dialogue_generation_service import UnityDialogueGenerationService
from services.graph_generation_service import GraphGenerationService
from core.llm.llm_client import ILLMClient
from core.context.context_builder import ContextBuilder
from api.container import ServiceContainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/unity-dialogues/graph", tags=["Graph Editor"])


@router.post(
    "/load",
    response_model=LoadGraphResponse,
    status_code=status.HTTP_200_OK
)
async def load_graph(
    request_data: LoadGraphRequest,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> LoadGraphResponse:
    """Charge un dialogue Unity JSON et le convertit en format graphe (nodes/edges).
    
    Args:
        request_data: Contenu JSON Unity.
        request_id: ID de la requête.
        
    Returns:
        Nœuds et edges ReactFlow avec métadonnées.
        
    Raises:
        ValidationException: Si le JSON est invalide.
        InternalServerException: Si la conversion échoue.
    """
    try:
        # Convertir Unity JSON → ReactFlow
        nodes, edges = GraphConversionService.unity_json_to_graph(request_data.json_content)
        
        # Calculer les métadonnées
        metadata = GraphMetadata(
            title="Dialogue Unity",
            node_count=len(nodes),
            edge_count=len(edges)
        )
        
        logger.info(
            f"Graphe chargé: {metadata.node_count} nœuds, "
            f"{metadata.edge_count} edges (request_id: {request_id})"
        )
        
        return LoadGraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )
        
    except ValueError as e:
        logger.warning(f"Validation error lors du chargement (request_id: {request_id}): {e}")
        raise ValidationException(
            message=str(e),
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"Erreur lors du chargement du graphe (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors du chargement du graphe",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/save",
    response_model=SaveGraphResponse,
    status_code=status.HTTP_200_OK
)
async def save_graph(
    request_data: SaveGraphRequest,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> SaveGraphResponse:
    """Sauvegarde un graphe modifié (reconvertit en Unity JSON).
    
    Args:
        request_data: Nœuds et edges ReactFlow avec métadonnées.
        request_id: ID de la requête.
        
    Returns:
        Nom de fichier et contenu JSON Unity généré.
        
    Raises:
        ValidationException: Si la conversion échoue.
        InternalServerException: Si la sauvegarde échoue.
    """
    try:
        # Convertir ReactFlow → Unity JSON
        json_content = GraphConversionService.graph_to_unity_json(
            request_data.nodes,
            request_data.edges
        )
        
        # Générer un nom de fichier (titre sanitizé)
        import re
        sanitized_title = re.sub(r'[^\w\s-]', '', request_data.metadata.title)
        sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title)
        filename = f"{sanitized_title}.json"
        
        logger.info(
            f"Graphe sauvegardé: {filename}, "
            f"{request_data.metadata.node_count} nœuds (request_id: {request_id})"
        )
        
        return SaveGraphResponse(
            success=True,
            filename=filename,
            json_content=json_content
        )
        
    except ValueError as e:
        logger.warning(f"Validation error lors de la sauvegarde (request_id: {request_id}): {e}")
        raise ValidationException(
            message=str(e),
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"Erreur lors de la sauvegarde du graphe (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la sauvegarde du graphe",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/generate-node",
    response_model=GenerateNodeResponse,
    status_code=status.HTTP_200_OK
)
async def generate_node(
    request_data: GenerateNodeRequest,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> GenerateNodeResponse:
    """Génère un nœud en contexte (extension de /generate/unity-dialogue).
    
    Args:
        request_data: Contexte parent et instructions de génération.
        request_id: ID de la requête.
        
    Returns:
        Nœud généré avec connexions suggérées.
        
    Raises:
        InternalServerException: Si la génération échoue.
    """
    try:
        # Obtenir le service container et les services nécessaires
        container = ServiceContainer()
        config_service = container.get_config_service()
        
        # Import local pour éviter les imports circulaires
        from factories.llm_factory import LLMClientFactory
        
        # Générer le client LLM
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=config_service.get_llm_config(),
            available_models=config_service.get_available_llm_models(),
        )
        
        generation_service = UnityDialogueGenerationService()
        parent_content = request_data.parent_node_content
        parent_choices = parent_content.get("choices", [])
        
        if request_data.generate_all_choices and not parent_choices:
            raise ValidationException(
                message="Aucun choix disponible pour la génération batch.",
                request_id=request_id
            )
        
        # Gérer génération batch si generate_all_choices=True
        if request_data.generate_all_choices and parent_choices:
            # Si les instructions sont vides, utiliser un texte par défaut
            user_instructions = request_data.user_instructions.strip() if request_data.user_instructions else ""
            if not user_instructions:
                user_instructions = "Ecris la réponse du PNJ à ce que dit le PJ"
            
            # Utiliser le service batch pour générer tous les choix
            graph_generation_service = GraphGenerationService(generation_service)
            batch_result = await graph_generation_service.generate_nodes_for_all_choices(
                parent_node=parent_content,
                instructions=user_instructions,
                context=request_data.context_selections,
                llm_client=llm_client,
                system_prompt_override=request_data.system_prompt_override,
                max_choices=request_data.max_choices
            )
            
            # Retourner tous les nœuds générés en batch
            failed_choices = batch_result.get("failed_choices", [])
            batch_count = len(batch_result["nodes"])
            connected_choices_count = batch_result.get("connected_choices_count")
            generated_choices_count = batch_result.get("generated_choices_count")
            failed_choices_count = batch_result.get("failed_choices_count")
            total_choices_count = batch_result.get("total_choices_count")
            
            if batch_result["nodes"]:
                suggested_connections = [
                    SuggestedConnection(**conn) for conn in batch_result["connections"]
                ]
                
                # Logger les résultats (succès et échecs)
                if failed_choices:
                    logger.warning(
                        f"Génération batch partielle: {batch_count} nœud(s) généré(s), "
                        f"{len(failed_choices)} échec(s) pour parent {request_data.parent_node_id} "
                        f"(request_id: {request_id})"
                    )
                else:
                    logger.info(
                        f"Génération batch: {batch_count} nœud(s) généré(s) "
                        f"pour parent {request_data.parent_node_id} (request_id: {request_id})"
                    )
                
                # Retourner tous les nœuds avec le premier pour backward compatibility
                return GenerateNodeResponse(
                    node=batch_result["nodes"][0] if batch_result["nodes"] else None,
                    nodes=batch_result["nodes"],
                    suggested_connections=suggested_connections,
                    parent_node_id=request_data.parent_node_id,
                    batch_count=batch_count,
                    generated_choices_count=generated_choices_count,
                    connected_choices_count=connected_choices_count,
                    failed_choices_count=failed_choices_count,
                    total_choices_count=total_choices_count
                )
            else:
                # Aucun nœud généré
                if failed_choices:
                    # Tous les choix ont échoué
                    error_msg = (
                        f"Aucun nœud généré. {len(failed_choices)} échec(s) de génération. "
                        f"Vérifiez les logs pour plus de détails."
                    )
                else:
                    # Tous les choix déjà connectés
                    error_msg = "Tous les choix sont déjà connectés. Aucun nœud à générer."
                
                raise ValidationException(
                    message=error_msg,
                    request_id=request_id
                )
        
        # Génération normale (choix spécifique ou nextNode)
        # Enrichir les instructions avec le contexte parent
        parent_speaker = parent_content.get("speaker", "PNJ")
        parent_line = parent_content.get("line", "")
        
        # Si les instructions sont vides, utiliser un texte par défaut
        user_instructions = request_data.user_instructions.strip() if request_data.user_instructions else ""
        if not user_instructions:
            user_instructions = "Ecris la réponse du PNJ à ce que dit le PJ"
        
        # Si target_choice_index est fourni, inclure le texte du choix correspondant
        if request_data.target_choice_index is not None and parent_choices:
            choice_index = request_data.target_choice_index
            if not (0 <= choice_index < len(parent_choices)):
                raise ValidationException(
                    message=f"Index de choix invalide: {choice_index}.",
                    request_id=request_id
                )
            
            choice_text = parent_choices[choice_index].get("text", "")
            enriched_instructions = f"""Contexte précédent:
{parent_speaker}: {parent_line}

Réponse du joueur:
{choice_text}

Instructions pour la suite:
{user_instructions}
"""
        elif request_data.target_choice_index is not None and not parent_choices:
            raise ValidationException(
                message="Aucun choix disponible pour la génération d'un choix spécifique.",
                request_id=request_id
            )
        else:
            # Pas de choix spécifique (nextNode ou génération normale)
            enriched_instructions = f"""Contexte précédent:
{parent_speaker}: {parent_line}

Instructions pour la suite:
{user_instructions}
"""
        
        # Pour la génération normale, on utilise juste les instructions enrichies comme prompt string
        # (le service generate_dialogue_node attend un string, pas un BuiltPrompt)
        response = await generation_service.generate_dialogue_node(
            llm_client=llm_client,
            prompt=enriched_instructions,
            system_prompt_override=request_data.system_prompt_override,
            max_choices=request_data.max_choices
        )
        
        # Déterminer l'ID de départ selon le mode de génération
        normalized_parent_id = (
            request_data.parent_node_id
            if request_data.parent_node_id.startswith("NODE_")
            else f"NODE_{request_data.parent_node_id}"
        )
        if request_data.target_choice_index is not None:
            # Génération pour choix spécifique : utiliser format CHOICE_{index}
            start_id = f"{normalized_parent_id}_CHOICE_{request_data.target_choice_index}"
        elif parent_choices:
            # Génération pour choix (premier sans targetNode) : utiliser format CHILD
            start_id = f"{normalized_parent_id}_CHILD"
        else:
            # Génération nextNode (navigation linéaire) : utiliser format CHILD
            start_id = f"{normalized_parent_id}_CHILD"
        
        # Enrichir avec ID
        enriched_nodes = generation_service.enrich_with_ids(
            content=response,
            start_id=start_id
        )
        
        # Le premier nœud enrichi
        generated_node = enriched_nodes[0]
        
        # Créer les connexions suggérées
        suggested_connections = []
        
        # Connexion depuis le parent vers le nouveau nœud
        if request_data.target_choice_index is not None:
            # Connexion pour choix spécifique
            suggested_connections.append(
                SuggestedConnection(
                    **{
                        "from": request_data.parent_node_id,
                        "to": generated_node["id"],
                        "via_choice_index": request_data.target_choice_index,
                        "connection_type": "choice"
                    }
                )
            )
        elif parent_choices:
            # Suggérer de connecter le premier choix sans targetNode
            for i, choice in enumerate(parent_choices):
                if not choice.get("targetNode") or choice.get("targetNode") == "END":
                    suggested_connections.append(
                        SuggestedConnection(
                            **{
                                "from": request_data.parent_node_id,
                                "to": generated_node["id"],
                                "via_choice_index": i,
                                "connection_type": "choice"
                            }
                        )
                    )
                    break
        else:
            # Connexion via nextNode
            suggested_connections.append(
                SuggestedConnection(
                    **{
                        "from": request_data.parent_node_id,
                        "to": generated_node["id"],
                        "connection_type": "nextNode"
                    }
                )
            )
        
        logger.info(
            f"Nœud généré en contexte: {generated_node['id']}, "
            f"parent: {request_data.parent_node_id} (request_id: {request_id})"
        )
        
        return GenerateNodeResponse(
            node=generated_node,
            suggested_connections=suggested_connections,
            parent_node_id=request_data.parent_node_id
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de la génération de nœud (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la génération de nœud",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/validate",
    response_model=ValidateGraphResponse,
    status_code=status.HTTP_200_OK
)
async def validate_graph(
    request_data: ValidateGraphRequest,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> ValidateGraphResponse:
    """Valide un graphe (nœuds orphelins, références cassées, cycles).
    
    Args:
        request_data: Nœuds et edges à valider.
        request_id: ID de la requête.
        
    Returns:
        Résultat de validation avec erreurs et warnings.
    """
    try:
        # Valider le graphe
        validation_result = GraphValidationService.validate_graph(
            request_data.nodes,
            request_data.edges
        )
        
        # Convertir en schéma Pydantic
        errors = [
            ValidationErrorDetail(**e.to_dict())
            for e in validation_result.errors
        ]
        
        warnings = [
            ValidationErrorDetail(**w.to_dict())
            for w in validation_result.warnings
        ]
        
        logger.info(
            f"Validation effectuée: {len(errors)} erreurs, "
            f"{len(warnings)} warnings (request_id: {request_id})"
        )
        
        return ValidateGraphResponse(
            valid=validation_result.valid,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de la validation (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la validation du graphe",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/calculate-layout",
    response_model=CalculateLayoutResponse,
    status_code=status.HTTP_200_OK
)
async def calculate_layout(
    request_data: CalculateLayoutRequest,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> CalculateLayoutResponse:
    """Calcule un layout automatique pour le graphe.
    
    Note: Pour Dagre, le calcul réel sera fait côté frontend avec dagre.js.
    Cette endpoint retourne un layout basique en cascade.
    
    Args:
        request_data: Nœuds, edges et paramètres de layout.
        request_id: ID de la requête.
        
    Returns:
        Nœuds avec positions calculées.
    """
    try:
        # Calculer le layout
        laid_out_nodes = GraphConversionService.calculate_layout(
            request_data.nodes,
            request_data.edges,
            request_data.algorithm,
            request_data.direction
        )
        
        logger.info(
            f"Layout calculé: {len(laid_out_nodes)} nœuds, "
            f"algorithme: {request_data.algorithm} (request_id: {request_id})"
        )
        
        return CalculateLayoutResponse(nodes=laid_out_nodes)
        
    except Exception as e:
        logger.exception(f"Erreur lors du calcul de layout (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors du calcul de layout",
            details={"error": str(e)},
            request_id=request_id
        )
