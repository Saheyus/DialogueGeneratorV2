"""Middleware de rate limiting pour les endpoints d'authentification."""
import logging
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from api.config.security_config import get_security_config

logger = logging.getLogger(__name__)


def get_rate_limiter() -> Optional[Limiter]:
    """Retourne une instance de Limiter si le rate limiting est activé.
    
    Returns:
        Instance de Limiter si activé, None sinon.
    """
    security_config = get_security_config()
    
    if not security_config.auth_rate_limit_enabled:
        logger.info("Rate limiting désactivé")
        return None
    
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[],  # Pas de limite globale par défaut
        storage_uri="memory://"  # Stockage en mémoire (suffisant pour la plupart des cas)
    )
    
    logger.info(
        f"Rate limiting activé: {security_config.auth_rate_limit_requests} "
        f"requêtes par {security_config.auth_rate_limit_window} secondes"
    )
    
    return limiter


# Instance globale du rate limiter
_rate_limiter: Optional[Limiter] = None


def get_limiter() -> Optional[Limiter]:
    """Retourne l'instance globale du rate limiter (singleton).
    
    Returns:
        Instance de Limiter si activé, None sinon.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = get_rate_limiter()
    return _rate_limiter


def get_rate_limit_string() -> str:
    """Retourne la chaîne de limite de taux au format slowapi.
    
    Returns:
        Chaîne de limite (ex: "5/minute").
    """
    security_config = get_security_config()
    return f"{security_config.auth_rate_limit_requests}/{security_config.auth_rate_limit_window} seconds"


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handler personnalisé pour les erreurs de rate limiting.
    
    Args:
        request: La requête HTTP.
        exc: L'exception RateLimitExceeded.
        
    Returns:
        Réponse JSON avec erreur 429.
    """
    from fastapi.responses import JSONResponse
    
    security_config = get_security_config()
    window_seconds = security_config.auth_rate_limit_window
    
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Trop de requêtes. Limite: {security_config.auth_rate_limit_requests} requêtes par {window_seconds} secondes.",
                "details": {
                    "limit": security_config.auth_rate_limit_requests,
                    "window_seconds": window_seconds,
                    "retry_after": window_seconds
                },
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        },
        headers={
            "X-RateLimit-Limit": str(security_config.auth_rate_limit_requests),
            "X-RateLimit-Window": str(window_seconds),
            "Retry-After": str(window_seconds)
        }
    )


def create_rate_limit_exception_handler():
    """Retourne le handler pour les exceptions de rate limiting.
    
    Returns:
        Handler pour RateLimitExceeded.
    """
    return rate_limit_exception_handler

