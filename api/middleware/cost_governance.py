"""Middleware pour la gouvernance des coûts LLM."""
import json
import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from services.cost_governance_service import CostGovernanceService
from services.llm_pricing_service import LLMPricingService
from api.dependencies import get_cost_governance_service, get_cost_budget_repository
from constants import ModelNames, Defaults

logger = logging.getLogger(__name__)

# User ID par défaut (V1.0: pas d'authentification, utilisateur unique)
DEFAULT_USER_ID = "default_user"

# Endpoints à intercepter pour vérification budget
GENERATION_ENDPOINTS = [
    "/api/v1/dialogues/generate/unity-dialogue",
    "/api/v1/dialogues/generate/variants",
    "/api/v1/graph/generate-node",
    "/api/v1/dialogues/generate/jobs",  # Streaming generation
]

# Estimation par défaut des tokens (si non disponibles dans la requête)
DEFAULT_PROMPT_TOKENS = 5000  # Estimation conservatrice
DEFAULT_COMPLETION_TOKENS = 1000  # Estimation conservatrice


class CostGovernanceMiddleware(BaseHTTPMiddleware):
    """Middleware pour vérifier le budget avant génération LLM.
    
    Intercepte les requêtes POST vers les endpoints de génération,
    estime le coût, vérifie le budget, et bloque si nécessaire.
    """
    
    def __init__(self, app):
        """Initialise le middleware.
        
        Args:
            app: L'application ASGI.
        """
        super().__init__(app)
        self.pricing_service = LLMPricingService()
        # Le service sera créé à chaque requête via dependency injection
        # pour éviter les problèmes de cycle de vie
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Vérifie le budget avant génération.
        
        Args:
            request: La requête HTTP.
            call_next: La fonction suivante dans la chaîne middleware.
            
        Returns:
            La réponse HTTP (429 si budget dépassé, sinon réponse normale).
        """
        # Vérifier si c'est une requête POST vers un endpoint de génération
        if request.method != "POST":
            return await call_next(request)
        
        path = request.url.path
        if not any(path.startswith(endpoint) for endpoint in GENERATION_ENDPOINTS):
            return await call_next(request)
        
        try:
            # Créer le service de cost governance
            repository = get_cost_budget_repository()
            cost_service = CostGovernanceService(repository=repository)
            
            # Estimer le coût
            estimated_cost = await self._estimate_cost(request)
            
            # Vérifier le budget
            budget_check = cost_service.check_budget(
                user_id=DEFAULT_USER_ID,
                estimated_cost=estimated_cost
            )
            
            # Si bloqué, retourner HTTP 429
            if not budget_check["allowed"]:
                logger.warning(
                    f"Génération bloquée pour {path}: budget dépassé ({budget_check['percentage']:.1f}%)"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "QUOTA_EXCEEDED",
                            "message": budget_check.get("warning", "Monthly quota reached"),
                            "details": {
                                "percentage": budget_check["percentage"],
                                "estimated_cost": estimated_cost
                            }
                        }
                    }
                )
            
            # Si warning (90%), logger mais continuer
            if budget_check.get("warning"):
                logger.warning(
                    f"Budget warning pour {path}: {budget_check['warning']} "
                    f"({budget_check['percentage']:.1f}%)"
                )
            
            # Continuer avec la requête
            return await call_next(request)
            
        except Exception as e:
            # En cas d'erreur, logger et continuer (ne pas bloquer la génération)
            logger.error(f"Erreur dans CostGovernanceMiddleware: {e}", exc_info=True)
            return await call_next(request)
    
    async def _estimate_cost(self, request: Request) -> float:
        """Estime le coût d'une génération basé sur la requête.
        
        Args:
            request: La requête HTTP.
            
        Returns:
            Coût estimé en USD.
        """
        try:
            # Lire le body de la requête (une seule fois)
            # Note: FastAPI/Starlette permet de lire le body plusieurs fois via request._body
            # mais pour être sûr, on utilise une approche non-destructive
            if hasattr(request, "_body"):
                body = request._body
            else:
                body = await request.body()
                # Stocker pour réutilisation (si possible)
                if hasattr(request, "_body"):
                    request._body = body
            
            # Si le body est vide, utiliser les valeurs par défaut
            if not body:
                return self._calculate_cost_with_defaults()
            
            # Parser le JSON
            try:
                body_data = json.loads(body)
            except json.JSONDecodeError:
                # Si le parsing échoue, utiliser les valeurs par défaut
                return self._calculate_cost_with_defaults()
            
            # Extraire le modèle (si disponible)
            model_name = body_data.get("model_name") or body_data.get("model") or Defaults.MODEL_ID
            
            # Essayer d'extraire les tokens estimés (si disponibles)
            prompt_tokens = body_data.get("token_count") or body_data.get("prompt_tokens") or DEFAULT_PROMPT_TOKENS
            completion_tokens = body_data.get("max_completion_tokens") or body_data.get("completion_tokens") or DEFAULT_COMPLETION_TOKENS
            
            # Calculer le coût
            cost = self.pricing_service.calculate_cost(
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            return cost
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'estimation du coût: {e}, utilisation des valeurs par défaut")
            return self._calculate_cost_with_defaults()
    
    def _calculate_cost_with_defaults(self) -> float:
        """Calcule le coût avec les valeurs par défaut.
        
        Returns:
            Coût estimé en USD avec valeurs par défaut.
        """
        return self.pricing_service.calculate_cost(
            model_name=Defaults.MODEL_ID,
            prompt_tokens=DEFAULT_PROMPT_TOKENS,
            completion_tokens=DEFAULT_COMPLETION_TOKENS
        )
