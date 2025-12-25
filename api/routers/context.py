"""Router pour le contexte GDD."""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from api.schemas.context import (
    CharacterListResponse,
    CharacterResponse,
    LocationListResponse,
    LocationResponse,
    ItemListResponse,
    ItemResponse,
    BuildContextRequest,
    BuildContextResponse
)
from api.schemas.dialogue import EstimateTokensRequest, EstimateTokensResponse
from api.dependencies import (
    get_context_builder,
    get_request_id
)
from api.exceptions import NotFoundException, InternalServerException
from context_builder import ContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/characters",
    response_model=CharacterListResponse,
    status_code=status.HTTP_200_OK
)
async def list_characters(
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> CharacterListResponse:
    """Liste tous les personnages disponibles.
    
    Args:
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des personnages.
    """
    characters = context_builder.characters
    character_responses = [
        CharacterResponse(name=char.get("Nom", "Unknown"), data=char)
        for char in characters
    ]
    
    return CharacterListResponse(
        characters=character_responses,
        total=len(character_responses)
    )


@router.get(
    "/characters/{name}",
    response_model=CharacterResponse,
    status_code=status.HTTP_200_OK
)
async def get_character(
    name: str,
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> CharacterResponse:
    """Récupère un personnage par son nom.
    
    Args:
        name: Nom du personnage.
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Le personnage demandé.
        
    Raises:
        NotFoundException: Si le personnage n'existe pas.
    """
    character_data = context_builder.get_character_details_by_name(name)
    if character_data is None:
        raise NotFoundException(
            resource_type="Personnage",
            resource_id=name,
            request_id=request_id
        )
    
    return CharacterResponse(name=name, data=character_data)


@router.get(
    "/locations",
    response_model=LocationListResponse,
    status_code=status.HTTP_200_OK
)
async def list_locations(
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> LocationListResponse:
    """Liste tous les lieux disponibles.
    
    Args:
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des lieux.
    """
    locations = context_builder.locations
    location_responses = [
        LocationResponse(name=loc.get("Nom", "Unknown"), data=loc)
        for loc in locations
    ]
    
    return LocationListResponse(
        locations=location_responses,
        total=len(location_responses)
    )


@router.get(
    "/locations/{name}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK
)
async def get_location(
    name: str,
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> LocationResponse:
    """Récupère un lieu par son nom.
    
    Args:
        name: Nom du lieu.
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Le lieu demandé.
        
    Raises:
        NotFoundException: Si le lieu n'existe pas.
    """
    location_data = context_builder.get_location_details_by_name(name)
    if location_data is None:
        raise NotFoundException(
            resource_type="Lieu",
            resource_id=name,
            request_id=request_id
        )
    
    return LocationResponse(name=name, data=location_data)


@router.get(
    "/items",
    response_model=ItemListResponse,
    status_code=status.HTTP_200_OK
)
async def list_items(
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> ItemListResponse:
    """Liste tous les objets disponibles.
    
    Args:
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des objets.
    """
    items = context_builder.items
    item_responses = [
        ItemResponse(name=item.get("Nom", "Unknown"), data=item)
        for item in items
    ]
    
    return ItemListResponse(
        items=item_responses,
        total=len(item_responses)
    )


@router.post(
    "/build",
    response_model=BuildContextResponse,
    status_code=status.HTTP_200_OK
)
async def build_context(
    request_data: BuildContextRequest,
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> BuildContextResponse:
    """Construit un contexte personnalisé à partir de sélections GDD.
    
    Args:
        request_data: Données de la requête (sélections, instructions).
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Le contexte construit.
    """
    try:
        # Convertir ContextSelection en dict pour le service (avec préfixes underscore)
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        context_text = context_builder.build_context(
            selected_elements=context_selections_dict,
            scene_instruction=request_data.user_instructions,
            max_tokens=request_data.max_tokens,
            include_dialogue_type=request_data.include_dialogue_type
        )
        
        token_count = context_builder._count_tokens(context_text)
        
        return BuildContextResponse(
            context=context_text,
            token_count=token_count
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de la construction du contexte (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la construction du contexte",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/estimate-tokens",
    response_model=EstimateTokensResponse,
    status_code=status.HTTP_200_OK
)
async def estimate_context_tokens(
    request_data: EstimateTokensRequest,
    request: Request,
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> EstimateTokensResponse:
    """Estime le nombre de tokens pour un contexte donné.
    
    Args:
        request_data: Données de la requête (sélections, instructions).
        request: La requête HTTP.
        context_builder: ContextBuilder injecté.
        request_id: ID de la requête.
        
    Returns:
        Estimation du nombre de tokens.
    """
    try:
        # Convertir ContextSelection en dict pour le service
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        context_text = context_builder.build_context(
            selected_elements=context_selections_dict,
            scene_instruction=request_data.user_instructions,
            max_tokens=request_data.max_tokens
        )
        
        token_count = context_builder._count_tokens(context_text)
        
        return EstimateTokensResponse(
            context_tokens=token_count,
            total_estimated_tokens=token_count  # Pour le contexte seul
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de l'estimation de tokens (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de l'estimation de tokens",
            details={"error": str(e)},
            request_id=request_id
        )

