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
from llm_client import ILLMClient
from prompt_engine import PromptEngine
from context_builder import ContextBuilder
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
        # Créer le prompt avec contexte parent
        context_builder = ContextBuilder()
        prompt_engine = PromptEngine(context_builder)
        
        # Construire le contexte de continuation
        parent_content = request_data.parent_node_content
        parent_speaker = parent_content.get("speaker", "PNJ")
        parent_line = parent_content.get("line", "")
        
        # Enrichir les instructions avec le contexte parent
        enriched_instructions = f"""Contexte précédent:
{parent_speaker}: {parent_line}

Instructions pour la suite:
{request_data.user_instructions}
"""
        
        # Construire le prompt complet
        prompt = prompt_engine.build_prompt(
            user_instructions=enriched_instructions,
            context_selections=request_data.context_selections,
            max_context_tokens=4000,
            system_prompt_override=request_data.system_prompt_override
        )
        
        # Obtenir le service container et les services nécessaires
        container = ServiceContainer()
        config_service = container.get_config_service()
        
        # Import local pour éviter les imports circulaires
        from factories.llm_factory import LLMClientFactory
        
        # Générer le nœud avec LLMClientFactory
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=config_service.get_llm_config(),
            available_models=config_service.get_available_llm_models(),
        )
        
        generation_service = UnityDialogueGenerationService()
        response = await generation_service.generate_dialogue_node(
            llm_client=llm_client,
            prompt=prompt,
            system_prompt_override=request_data.system_prompt_override,
            max_choices=request_data.max_choices
        )
        
        # Enrichir avec ID
        enriched_nodes = generation_service.enrich_with_ids(
            content=response,
            start_id=f"NODE_{request_data.parent_node_id}_CHILD"
        )
        
        # Le premier nœud enrichi
        generated_node = enriched_nodes[0]
        
        # Créer les connexions suggérées
        suggested_connections = []
        
        # Connexion depuis le parent vers le nouveau nœud
        # Si le parent a des choix, on suggère de connecter un choix spécifique
        parent_choices = parent_content.get("choices", [])
        if parent_choices:
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
