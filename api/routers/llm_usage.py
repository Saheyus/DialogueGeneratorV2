"""Router pour les endpoints de suivi d'utilisation LLM."""
import logging
from datetime import date, datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from api.dependencies import get_llm_usage_service, get_request_id
from api.exceptions import InternalServerException
from api.schemas.llm_usage import (
    LLMUsageHistoryResponse,
    LLMUsageRecordResponse,
    LLMUsageStatisticsResponse
)
from api.utils.pagination import paginate_list, PaginationParams
from services.llm_usage_service import LLMUsageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/history",
    response_model=LLMUsageHistoryResponse,
    status_code=status.HTTP_200_OK
)
async def get_usage_history(
    request: Request,
    usage_service: Annotated[LLMUsageService, Depends(get_llm_usage_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    start_date: Optional[date] = Query(
        default=None,
        description="Date de début (incluse). Par défaut: 30 jours avant aujourd'hui."
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Date de fin (incluse). Par défaut: aujourd'hui."
    ),
    model: Optional[str] = Query(
        default=None,
        alias="model",
        description="Filtrer par nom de modèle (ex: gpt-4o)"
    ),
    page: int = Query(default=1, ge=1, description="Numéro de page"),
    page_size: int = Query(default=50, ge=1, le=200, description="Taille de la page")
) -> LLMUsageHistoryResponse:
    """Récupère l'historique d'utilisation LLM avec pagination.
    
    Args:
        request: La requête HTTP.
        usage_service: Service de tracking injecté.
        request_id: ID de la requête.
        start_date: Date de début (optionnel).
        end_date: Date de fin (optionnel).
        model: Filtrer par modèle (optionnel).
        page: Numéro de page.
        page_size: Taille de la page.
        
    Returns:
        Historique paginé des enregistrements d'utilisation.
        
    Raises:
        InternalServerException: Si la récupération échoue.
    """
    try:
        # Définir les dates par défaut si non fournies
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Récupérer l'historique
        records = usage_service.get_usage_history(
            start_date=start_date,
            end_date=end_date,
            model_name=model
        )
        
        # Paginer
        total = len(records)
        pagination_params = PaginationParams(page=page, page_size=page_size)
        paginated_records = paginate_list(records, pagination_params)
        total_pages = (total + page_size - 1) // page_size
        
        # Convertir en schémas de réponse
        record_responses = [
            LLMUsageRecordResponse(
                request_id=r.request_id,
                timestamp=r.timestamp,
                model_name=r.model_name,
                prompt_tokens=r.prompt_tokens,
                completion_tokens=r.completion_tokens,
                total_tokens=r.total_tokens,
                estimated_cost=r.estimated_cost,
                duration_ms=r.duration_ms,
                success=r.success,
                endpoint=r.endpoint,
                k_variants=r.k_variants,
                error_message=r.error_message
            )
            for r in paginated_records
        ]
        
        return LLMUsageHistoryResponse(
            records=record_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération de l'historique LLM (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la récupération de l'historique d'utilisation LLM",
            details={"error": str(e)},
            request_id=request_id
        )


@router.get(
    "/statistics",
    response_model=LLMUsageStatisticsResponse,
    status_code=status.HTTP_200_OK
)
async def get_usage_statistics(
    request: Request,
    usage_service: Annotated[LLMUsageService, Depends(get_llm_usage_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    start_date: Optional[date] = Query(
        default=None,
        description="Date de début (incluse). Par défaut: 30 jours avant aujourd'hui."
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Date de fin (incluse). Par défaut: aujourd'hui."
    ),
    model: Optional[str] = Query(
        default=None,
        alias="model",
        description="Filtrer par nom de modèle (ex: gpt-4o)"
    )
) -> LLMUsageStatisticsResponse:
    """Récupère les statistiques agrégées d'utilisation LLM.
    
    Args:
        request: La requête HTTP.
        usage_service: Service de tracking injecté.
        request_id: ID de la requête.
        start_date: Date de début (optionnel).
        end_date: Date de fin (optionnel).
        model: Filtrer par modèle (optionnel).
        
    Returns:
        Statistiques agrégées d'utilisation.
        
    Raises:
        InternalServerException: Si le calcul échoue.
    """
    try:
        # Définir les dates par défaut si non fournies
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Récupérer les statistiques
        stats = usage_service.get_statistics(
            start_date=start_date,
            end_date=end_date,
            model_name=model
        )
        
        return LLMUsageStatisticsResponse(
            total_tokens=stats["total_tokens"],
            total_prompt_tokens=stats["total_prompt_tokens"],
            total_completion_tokens=stats["total_completion_tokens"],
            total_cost=stats["total_cost"],
            calls_count=stats["calls_count"],
            success_count=stats["success_count"],
            error_count=stats["error_count"],
            success_rate=stats["success_rate"],
            avg_duration_ms=stats["avg_duration_ms"],
            start_date=start_date,
            end_date=end_date,
            model_name=model
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors du calcul des statistiques LLM (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors du calcul des statistiques d'utilisation LLM",
            details={"error": str(e)},
            request_id=request_id
        )

