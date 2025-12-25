"""Router pour les interactions (CRUD)."""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Request, status
from api.schemas.interaction import (
    InteractionResponse,
    InteractionCreateRequest,
    InteractionUpdateRequest,
    InteractionListResponse,
    InteractionRelationsResponse,
    InteractionContextPathResponse
)
from api.dependencies import (
    get_interaction_service,
    get_request_id
)
from api.exceptions import NotFoundException, ValidationException, InternalServerException
from services.interaction_service import InteractionService
from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dialogue_elements import (
    DialogueLineElement,
    PlayerChoicesBlockElement,
    CommandElement
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_elements(elements_data: list[dict]) -> list:
    """Parse les éléments depuis un format dict vers des objets Pydantic.
    
    Args:
        elements_data: Liste de dictionnaires représentant les éléments.
        
    Returns:
        Liste d'objets AnyDialogueElement.
    """
    parsed_elements = []
    for elem_data in elements_data:
        element_type = elem_data.get("element_type")
        if element_type == "dialogue_line":
            parsed_elements.append(DialogueLineElement(**elem_data))
        elif element_type == "player_choices_block":
            parsed_elements.append(PlayerChoicesBlockElement(**elem_data))
        elif element_type == "command":
            parsed_elements.append(CommandElement(**elem_data))
        else:
            logger.warning(f"Type d'élément inconnu ignoré: {element_type}")
    return parsed_elements


@router.get(
    "",
    response_model=InteractionListResponse,
    status_code=status.HTTP_200_OK
)
async def list_interactions(
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionListResponse:
    """Liste toutes les interactions.
    
    Args:
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des interactions.
    """
    try:
        interactions = interaction_service.get_all()
        interaction_responses = [InteractionResponse.from_model(interaction) for interaction in interactions]
        
        return InteractionListResponse(
            interactions=interaction_responses,
            total=len(interaction_responses)
        )
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération des interactions (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération des interactions",
            details={"error": str(e)},
            request_id=request_id
        )


@router.get(
    "/{interaction_id}",
    response_model=InteractionResponse,
    status_code=status.HTTP_200_OK
)
async def get_interaction(
    interaction_id: str,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionResponse:
    """Récupère une interaction par son ID.
    
    Args:
        interaction_id: ID de l'interaction.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        L'interaction demandée.
        
    Raises:
        NotFoundException: Si l'interaction n'existe pas.
    """
    interaction = interaction_service.get_by_id(interaction_id)
    if interaction is None:
        raise NotFoundException(
            resource_type="Interaction",
            resource_id=interaction_id,
            request_id=request_id
        )
    
    return InteractionResponse.from_model(interaction)


@router.post(
    "",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_interaction(
    request_data: InteractionCreateRequest,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionResponse:
    """Crée une nouvelle interaction.
    
    Args:
        request_data: Données de la nouvelle interaction.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        L'interaction créée.
        
    Raises:
        ValidationException: Si les données sont invalides.
    """
    try:
        # Parser les éléments
        parsed_elements = _parse_elements(request_data.elements)
        
        # Créer l'interaction
        interaction = interaction_service.create_interaction(
            title=request_data.title,
            elements=parsed_elements,
            header_commands=request_data.header_commands,
            header_tags=request_data.header_tags
        )
        
        return InteractionResponse.from_model(interaction)
        
    except Exception as e:
        logger.exception(f"Erreur lors de la création de l'interaction (request_id: {request_id})")
        raise ValidationException(
            message="Erreur lors de la création de l'interaction",
            details={"error": str(e)},
            request_id=request_id
        )


@router.put(
    "/{interaction_id}",
    response_model=InteractionResponse,
    status_code=status.HTTP_200_OK
)
async def update_interaction(
    interaction_id: str,
    request_data: InteractionUpdateRequest,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionResponse:
    """Met à jour une interaction existante.
    
    Args:
        interaction_id: ID de l'interaction à mettre à jour.
        request_data: Données de mise à jour.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        L'interaction mise à jour.
        
    Raises:
        NotFoundException: Si l'interaction n'existe pas.
        ValidationException: Si les données sont invalides.
    """
    # Vérifier que l'interaction existe
    existing = interaction_service.get_by_id(interaction_id)
    if existing is None:
        raise NotFoundException(
            resource_type="Interaction",
            resource_id=interaction_id,
            request_id=request_id
        )
    
    try:
        # Mettre à jour les champs fournis
        update_data = request_data.model_dump(exclude_unset=True)
        
        if "elements" in update_data and update_data["elements"] is not None:
            parsed_elements = _parse_elements(update_data["elements"])
            existing.elements = parsed_elements
        
        if "title" in update_data and update_data["title"] is not None:
            existing.title = update_data["title"]
        
        if "header_commands" in update_data and update_data["header_commands"] is not None:
            existing.header_commands = update_data["header_commands"]
        
        if "header_tags" in update_data and update_data["header_tags"] is not None:
            existing.header_tags = update_data["header_tags"]
        
        if "next_interaction_id_if_no_choices" in update_data:
            existing.next_interaction_id_if_no_choices = update_data["next_interaction_id_if_no_choices"]
        
        # Sauvegarder
        interaction_service.save(existing)
        
        return InteractionResponse.from_model(existing)
        
    except Exception as e:
        logger.exception(f"Erreur lors de la mise à jour de l'interaction (request_id: {request_id})")
        raise ValidationException(
            message="Erreur lors de la mise à jour de l'interaction",
            details={"error": str(e)},
            request_id=request_id
        )


@router.delete(
    "/{interaction_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_interaction(
    interaction_id: str,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> None:
    """Supprime une interaction.
    
    Args:
        interaction_id: ID de l'interaction à supprimer.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Raises:
        NotFoundException: Si l'interaction n'existe pas.
    """
    if not interaction_service.exists(interaction_id):
        raise NotFoundException(
            resource_type="Interaction",
            resource_id=interaction_id,
            request_id=request_id
        )
    
    interaction_service.delete(interaction_id)
    logger.info(f"Interaction '{interaction_id}' supprimée (request_id: {request_id})")


@router.get(
    "/{interaction_id}/parents",
    response_model=InteractionRelationsResponse,
    status_code=status.HTTP_200_OK
)
async def get_interaction_parents(
    interaction_id: str,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionRelationsResponse:
    """Récupère les interactions parentes d'une interaction.
    
    Args:
        interaction_id: ID de l'interaction.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des IDs des interactions parentes.
        
    Raises:
        NotFoundException: Si l'interaction n'existe pas.
    """
    if not interaction_service.exists(interaction_id):
        raise NotFoundException(
            resource_type="Interaction",
            resource_id=interaction_id,
            request_id=request_id
        )
    
    parents = interaction_service.get_parent_interactions(interaction_id)
    parent_ids = [parent.interaction_id for parent in parents]
    
    return InteractionRelationsResponse(parents=parent_ids, children=[])


@router.get(
    "/{interaction_id}/children",
    response_model=InteractionRelationsResponse,
    status_code=status.HTTP_200_OK
)
async def get_interaction_children(
    interaction_id: str,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionRelationsResponse:
    """Récupère les interactions enfants d'une interaction.
    
    Args:
        interaction_id: ID de l'interaction.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des IDs des interactions enfants.
        
    Raises:
        NotFoundException: Si l'interaction n'existe pas.
    """
    if not interaction_service.exists(interaction_id):
        raise NotFoundException(
            resource_type="Interaction",
            resource_id=interaction_id,
            request_id=request_id
        )
    
    children = interaction_service.get_child_interactions(interaction_id)
    child_ids = [child.interaction_id for child in children]
    
    return InteractionRelationsResponse(parents=[], children=child_ids)


@router.get(
    "/{interaction_id}/context-path",
    response_model=InteractionContextPathResponse,
    status_code=status.HTTP_200_OK
)
async def get_interaction_context_path(
    interaction_id: str,
    request: Request,
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> InteractionContextPathResponse:
    """Récupère le chemin complet de contexte d'une interaction (tous les parents jusqu'à la racine).
    
    Args:
        interaction_id: ID de l'interaction.
        request: La requête HTTP.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        Chemin complet des interactions (de la racine à l'interaction cible).
        
    Raises:
        NotFoundException: Si l'interaction n'existe pas.
    """
    if not interaction_service.exists(interaction_id):
        raise NotFoundException(
            resource_type="Interaction",
            resource_id=interaction_id,
            request_id=request_id
        )
    
    # Récupérer le chemin complet (tous les parents jusqu'à la racine)
    path_interactions = interaction_service.get_dialogue_path(interaction_id)
    
    # Convertir en format de réponse
    path_responses = [InteractionResponse.from_model(interaction) for interaction in path_interactions]
    
    return InteractionContextPathResponse(
        path=path_responses,
        total=len(path_responses)
    )

