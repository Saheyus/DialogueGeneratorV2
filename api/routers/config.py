"""Router pour la configuration."""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from api.dependencies import (
    get_config_service,
    get_request_id
)
from api.exceptions import InternalServerException
from services.configuration_service import ConfigurationService

logger = logging.getLogger(__name__)

router = APIRouter()


class LLMConfigResponse(BaseModel):
    """Réponse contenant la configuration LLM.
    
    Attributes:
        config: Configuration LLM complète.
    """
    config: dict


class LLMModelResponse(BaseModel):
    """Réponse contenant un modèle LLM.
    
    Attributes:
        model_identifier: Identifiant du modèle.
        display_name: Nom d'affichage.
        client_type: Type de client (openai, dummy, etc.).
        max_tokens: Nombre maximum de tokens.
    """
    model_identifier: str
    display_name: str
    client_type: str
    max_tokens: int


class LLMModelsListResponse(BaseModel):
    """Réponse contenant la liste des modèles LLM disponibles.
    
    Attributes:
        models: Liste des modèles.
        total: Nombre total de modèles.
    """
    models: list[LLMModelResponse]
    total: int


class ContextConfigResponse(BaseModel):
    """Réponse contenant la configuration de contexte.
    
    Attributes:
        config: Configuration de contexte complète.
    """
    config: dict


class UnityDialoguesPathRequest(BaseModel):
    """Requête pour configurer le chemin des dialogues Unity.
    
    Attributes:
        path: Chemin vers le dossier Unity des dialogues.
    """
    path: str = Field(..., description="Chemin vers le dossier Unity des dialogues")


class UnityDialoguesPathResponse(BaseModel):
    """Réponse contenant le chemin configuré des dialogues Unity.
    
    Attributes:
        path: Chemin vers le dossier Unity des dialogues.
    """
    path: str = Field(..., description="Chemin vers le dossier Unity des dialogues")


@router.get(
    "/llm",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_200_OK
)
async def get_llm_config(
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> LLMConfigResponse:
    """Récupère la configuration LLM.
    
    Args:
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Configuration LLM.
    """
    try:
        llm_config = config_service.get_llm_config()
        return LLMConfigResponse(config=llm_config)
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération de la config LLM (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération de la configuration LLM",
            details={"error": str(e)},
            request_id=request_id
        )


@router.put(
    "/llm",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_200_OK
)
async def update_llm_config(
    config_data: dict,
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> LLMConfigResponse:
    """Met à jour la configuration LLM.
    
    Args:
        config_data: Nouvelles données de configuration.
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Configuration LLM mise à jour.
    """
    try:
        # TODO: Implémenter la mise à jour dans ConfigurationService
        # Pour l'instant, on retourne juste la config actuelle
        llm_config = config_service.get_llm_config()
        return LLMConfigResponse(config=llm_config)
    except Exception as e:
        logger.exception(f"Erreur lors de la mise à jour de la config LLM (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la mise à jour de la configuration LLM",
            details={"error": str(e)},
            request_id=request_id
        )


@router.get(
    "/llm/models",
    response_model=LLMModelsListResponse,
    status_code=status.HTTP_200_OK
)
async def list_llm_models(
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> LLMModelsListResponse:
    """Liste tous les modèles LLM disponibles.
    
    Args:
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des modèles LLM.
    """
    try:
        available_models = config_service.get_available_llm_models()
        
        model_responses = [
            LLMModelResponse(
                model_identifier=model.get("model_identifier", "unknown"),
                display_name=model.get("display_name", model.get("model_identifier", "Unknown")),
                client_type=model.get("client_type", "unknown"),
                max_tokens=model.get("max_tokens", 4096)
            )
            for model in available_models
        ]
        
        return LLMModelsListResponse(
            models=model_responses,
            total=len(model_responses)
        )
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération des modèles LLM (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération des modèles LLM",
            details={"error": str(e)},
            request_id=request_id
        )


@router.get(
    "/context",
    response_model=ContextConfigResponse,
    status_code=status.HTTP_200_OK
)
async def get_context_config(
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> ContextConfigResponse:
    """Récupère la configuration de contexte.
    
    Args:
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Configuration de contexte.
    """
    try:
        context_config = config_service.get_context_config()
        return ContextConfigResponse(config=context_config)
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération de la config contexte (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération de la configuration de contexte",
            details={"error": str(e)},
            request_id=request_id
        )


@router.get(
    "/unity-dialogues-path",
    response_model=UnityDialoguesPathResponse,
    status_code=status.HTTP_200_OK
)
async def get_unity_dialogues_path(
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> UnityDialoguesPathResponse:
    """Récupère le chemin configuré des dialogues Unity.
    
    Args:
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Chemin configuré des dialogues Unity.
    """
    try:
        unity_path = config_service.get_unity_dialogues_path()
        if unity_path is None:
            return UnityDialoguesPathResponse(path="")
        return UnityDialoguesPathResponse(path=str(unity_path))
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération du chemin Unity (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération du chemin Unity",
            details={"error": str(e)},
            request_id=request_id
        )


@router.put(
    "/unity-dialogues-path",
    response_model=UnityDialoguesPathResponse,
    status_code=status.HTTP_200_OK
)
async def set_unity_dialogues_path(
    request_data: UnityDialoguesPathRequest,
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> UnityDialoguesPathResponse:
    """Configure le chemin des dialogues Unity.
    
    Args:
        request_data: Données de la requête (chemin).
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Chemin configuré des dialogues Unity.
        
    Raises:
        ValidationException: Si le chemin est invalide.
    """
    try:
        success = config_service.set_unity_dialogues_path(request_data.path)
        if not success:
            from api.exceptions import ValidationException
            raise ValidationException(
                message="Le chemin Unity fourni est invalide ou ne peut pas être créé",
                details={"path": request_data.path},
                request_id=request_id
            )
        
        unity_path = config_service.get_unity_dialogues_path()
        if unity_path is None:
            return UnityDialoguesPathResponse(path="")
        return UnityDialoguesPathResponse(path=str(unity_path))
    except ValidationException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de la configuration du chemin Unity (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la configuration du chemin Unity",
            details={"error": str(e)},
            request_id=request_id
        )

