"""Middleware pour enrichir le contexte des logs avec des informations de requête."""
import logging
from typing import Optional
from fastapi import Request
from api.dependencies import get_request_id


class LoggingContextAdapter(logging.LoggerAdapter):
    """Adapter de logger qui enrichit les logs avec le contexte de la requête.
    
    Permet d'ajouter automatiquement des informations contextuelles (request_id,
    user_id, endpoint, etc.) à tous les logs émis pendant le traitement d'une requête.
    """
    
    def process(self, msg: str, kwargs: dict) -> tuple:
        """Enrichit le message de log avec le contexte.
        
        Args:
            msg: Message de log original.
            kwargs: Arguments de log (peut contenir 'extra').
            
        Returns:
            Tuple (message, kwargs) avec le contexte enrichi.
        """
        # Extraire ou créer le dictionnaire 'extra'
        extra = kwargs.setdefault("extra", {})
        
        # Ajouter le contexte si disponible
        if hasattr(self, "context"):
            extra.update(self.context)
        
        return msg, kwargs


def get_logger_with_context(request: Optional[Request] = None, user_id: Optional[str] = None) -> logging.Logger:
    """Retourne un logger enrichi avec le contexte de la requête.
    
    Args:
        request: La requête HTTP (optionnel).
        user_id: ID de l'utilisateur authentifié (optionnel).
        
    Returns:
        Logger adapté avec contexte.
    """
    logger = logging.getLogger("api")
    
    if request is None:
        return logger
    
    # Construire le contexte
    context = {}
    
    # Request ID
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        context["request_id"] = request_id
    
    # User ID
    if user_id:
        context["user_id"] = user_id
    
    # Endpoint et méthode
    if hasattr(request, "url") and request.url:
        context["endpoint"] = request.url.path
    if hasattr(request, "method"):
        context["method"] = request.method
    
    # Environnement
    import os
    environment = os.getenv("ENVIRONMENT", "development")
    context["environment"] = environment
    
    # Créer l'adapter avec le contexte
    adapter = LoggingContextAdapter(logger, context)
    adapter.context = context
    
    return adapter


def add_logging_context_to_record(record: logging.LogRecord, request: Optional[Request] = None, **kwargs: dict) -> None:
    """Ajoute le contexte de logging à un LogRecord.
    
    Args:
        record: Le LogRecord à enrichir.
        request: La requête HTTP (optionnel).
        **kwargs: Contexte supplémentaire à ajouter (user_id, endpoint, etc.).
    """
    # Ajouter les kwargs directement comme attributs
    for key, value in kwargs.items():
        setattr(record, key, value)
    
    # Ajouter le contexte de la requête si disponible
    if request:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            record.request_id = request_id
        
        if hasattr(request, "url") and request.url:
            record.endpoint = request.url.path
        if hasattr(request, "method"):
            record.method = request.method
    
    # Ajouter l'environnement
    import os
    environment = os.getenv("ENVIRONMENT", "development")
    record.environment = environment





