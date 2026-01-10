"""Router pour la gestion des flags in-game (mécaniques RPG)."""
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from api.schemas.flags import (
    FlagsCatalogResponse,
    FlagDefinition,
    UpsertFlagRequest,
    UpsertFlagResponse,
    ToggleFavoriteRequest,
    ToggleFavoriteResponse
)
from api.exceptions import InternalServerException, ValidationException, NotFoundException
from api.dependencies import get_request_id
from services.flag_catalog_service import FlagCatalogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mechanics/flags", tags=["Mechanics - Flags"])


def get_flag_catalog_service() -> FlagCatalogService:
    """Retourne une instance du service de catalogue de flags.
    
    Returns:
        Instance de FlagCatalogService.
    """
    return FlagCatalogService()


@router.get(
    "",
    response_model=FlagsCatalogResponse,
    status_code=status.HTTP_200_OK
)
async def list_flags(
    q: Optional[str] = Query(None, description="Terme de recherche (id, label, description, tags)"),
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    favorites_only: bool = Query(False, description="Ne retourner que les favoris"),
    flag_service: Annotated[FlagCatalogService, Depends(get_flag_catalog_service)] = None,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> FlagsCatalogResponse:
    """Liste les définitions de flags disponibles avec filtres optionnels.
    
    Args:
        q: Terme de recherche textuelle.
        category: Filtrer par catégorie (ex: "Event", "Choice", "Stat").
        favorites_only: Ne retourner que les flags favoris.
        flag_service: Service de catalogue injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des définitions de flags correspondant aux critères.
    """
    try:
        flags = flag_service.search(
            query=q,
            category=category,
            favorites_only=favorites_only
        )
        
        # Convertir en modèles Pydantic
        flag_definitions = [FlagDefinition(**flag) for flag in flags]
        
        return FlagsCatalogResponse(
            flags=flag_definitions,
            total=len(flag_definitions)
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération des flags (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération des flags",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "",
    response_model=UpsertFlagResponse,
    status_code=status.HTTP_200_OK
)
async def upsert_flag(
    request_data: UpsertFlagRequest,
    flag_service: Annotated[FlagCatalogService, Depends(get_flag_catalog_service)] = None,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> UpsertFlagResponse:
    """Crée ou met à jour une définition de flag dans le catalogue.
    
    Args:
        request_data: Données de la définition du flag.
        flag_service: Service de catalogue injecté.
        request_id: ID de la requête.
        
    Returns:
        Réponse contenant la définition créée/mise à jour.
        
    Raises:
        ValidationException: Si la définition est invalide.
        InternalServerException: Si l'écriture échoue.
    """
    try:
        # Convertir en dict pour le service
        definition_dict = request_data.model_dump()
        
        # Upsert via le service
        flag_service.upsert_definition(definition_dict)
        
        # Recharger la définition depuis le CSV pour confirmation
        flag_service.reload()
        flags = flag_service.search(query=request_data.id)
        
        if not flags:
            raise InternalServerException(
                message="Le flag a été créé mais n'a pas pu être relu",
                request_id=request_id
            )
        
        updated_flag = FlagDefinition(**flags[0])
        
        return UpsertFlagResponse(
            success=True,
            flag=updated_flag
        )
        
    except ValueError as e:
        logger.warning(f"Validation error lors de l'upsert de flag (request_id: {request_id}): {e}")
        raise ValidationException(
            message=str(e),
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"Erreur lors de l'upsert de flag (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de l'upsert du flag",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/toggle-favorite",
    response_model=ToggleFavoriteResponse,
    status_code=status.HTTP_200_OK
)
async def toggle_favorite(
    request_data: ToggleFavoriteRequest,
    flag_service: Annotated[FlagCatalogService, Depends(get_flag_catalog_service)] = None,
    request_id: Annotated[str, Depends(get_request_id)] = None
) -> ToggleFavoriteResponse:
    """Active/désactive le statut favori d'un flag.
    
    Args:
        request_data: Données de la requête (flag_id, is_favorite).
        flag_service: Service de catalogue injecté.
        request_id: ID de la requête.
        
    Returns:
        Réponse de confirmation.
        
    Raises:
        NotFoundException: Si le flag n'existe pas.
        InternalServerException: Si l'écriture échoue.
    """
    try:
        flag_service.toggle_favorite(
            flag_id=request_data.flag_id,
            is_favorite=request_data.is_favorite
        )
        
        return ToggleFavoriteResponse(
            success=True,
            flag_id=request_data.flag_id,
            is_favorite=request_data.is_favorite
        )
        
    except ValueError as e:
        # Flag introuvable
        logger.warning(f"Flag introuvable (request_id: {request_id}): {e}")
        raise NotFoundException(
            resource_type="Flag",
            resource_id=request_data.flag_id,
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"Erreur lors du toggle favorite (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors du toggle favorite",
            details={"error": str(e)},
            request_id=request_id
        )
