"""Service de tracking de l'utilisation des LLM."""
import logging
import time
from datetime import date, datetime, UTC
from typing import Dict, List, Optional

from models.llm_usage import LLMUsageRecord
from services.llm_pricing_service import LLMPricingService
from services.repositories.llm_usage_repository import ILLMUsageRepository

logger = logging.getLogger(__name__)


class LLMUsageService:
    """Service principal pour le tracking de l'utilisation LLM.
    
    Gère l'enregistrement des appels LLM et le calcul des statistiques.
    """
    
    def __init__(
        self,
        repository: ILLMUsageRepository,
        pricing_service: Optional[LLMPricingService] = None
    ):
        """Initialise le service de tracking.
        
        Args:
            repository: Repository pour stocker les enregistrements.
            pricing_service: Service de calcul des prix. Si None, en crée un nouveau.
        """
        self.repository = repository
        self.pricing_service = pricing_service or LLMPricingService()
        logger.info("LLMUsageService initialisé")
    
    def track_usage(
        self,
        request_id: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        duration_ms: int,
        success: bool,
        endpoint: str,
        k_variants: int = 1,
        error_message: Optional[str] = None
    ) -> None:
        """Enregistre un appel LLM.
        
        Args:
            request_id: ID de la requête API.
            model_name: Nom du modèle utilisé.
            prompt_tokens: Nombre de tokens dans le prompt.
            completion_tokens: Nombre de tokens dans la réponse.
            total_tokens: Nombre total de tokens.
            duration_ms: Durée de l'appel en millisecondes.
            success: Indique si l'appel a réussi.
            endpoint: Endpoint appelé.
            k_variants: Nombre de variantes générées.
            error_message: Message d'erreur si success=False.
        """
        try:
            # Calculer le coût estimé
            estimated_cost = self.pricing_service.calculate_cost(
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Créer l'enregistrement
            record = LLMUsageRecord(
                request_id=request_id,
                timestamp=datetime.now(UTC),
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                duration_ms=duration_ms,
                success=success,
                endpoint=endpoint,
                k_variants=k_variants,
                error_message=error_message
            )
            
            # Sauvegarder
            self.repository.save(record)
            
            logger.debug(
                f"Usage LLM enregistré: {model_name}, "
                f"{total_tokens} tokens, ${estimated_cost:.6f}, "
                f"{duration_ms}ms, success={success}"
            )
        except Exception as e:
            # Ne pas faire échouer l'appel LLM si le tracking échoue
            logger.error(f"Erreur lors de l'enregistrement de l'usage LLM: {e}", exc_info=True)
    
    def get_usage_history(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        model_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[LLMUsageRecord]:
        """Récupère l'historique d'utilisation avec filtres.
        
        Args:
            start_date: Date de début (optionnel).
            end_date: Date de fin (optionnel).
            model_name: Filtrer par modèle (optionnel).
            limit: Limiter le nombre de résultats (optionnel).
            
        Returns:
            Liste des enregistrements correspondants, triés par timestamp décroissant.
        """
        if start_date and end_date:
            records = self.repository.get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                model_name=model_name
            )
        else:
            records = self.repository.get_all(model_name=model_name)
        
        # Appliquer la limite si demandée
        if limit:
            records = records[:limit]
        
        return records
    
    def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        model_name: Optional[str] = None
    ) -> Dict:
        """Calcule des statistiques agrégées.
        
        Args:
            start_date: Date de début (optionnel).
            end_date: Date de fin (optionnel).
            model_name: Filtrer par modèle (optionnel).
            
        Returns:
            Dictionnaire avec les statistiques agrégées.
        """
        return self.repository.get_statistics(
            start_date=start_date,
            end_date=end_date,
            model_name=model_name
        )

