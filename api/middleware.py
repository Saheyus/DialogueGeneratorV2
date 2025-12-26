"""Middleware pour l'API FastAPI."""
import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware pour générer et ajouter un ID de requête à chaque requête."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Ajoute un request_id à chaque requête.
        
        Args:
            request: La requête HTTP.
            call_next: La fonction suivante dans la chaîne middleware.
            
        Returns:
            La réponse HTTP avec le request_id dans les headers.
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger les requêtes HTTP."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log les requêtes HTTP avec timing.
        
        Args:
            request: La requête HTTP.
            call_next: La fonction suivante dans la chaîne middleware.
            
        Returns:
            La réponse HTTP.
        """
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        # Log de la requête entrante
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"(request_id: {request_id}, client: {request.client.host if request.client else 'unknown'})"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log de la réponse
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s "
                f"(request_id: {request_id})"
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"Exception: {type(e).__name__}: {str(e)} "
                f"Time: {process_time:.3f}s "
                f"(request_id: {request_id})",
                exc_info=True
            )
            raise


class CORSMiddleware:
    """Middleware CORS personnalisé (alternative à celui de FastAPI si besoin de plus de contrôle)."""
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: list[str] = None,
        allow_credentials: bool = True,
        allow_methods: list[str] = None,
        allow_headers: list[str] = None
    ):
        """Initialise le middleware CORS.
        
        Args:
            app: L'application ASGI.
            allow_origins: Liste des origines autorisées (None = toutes).
            allow_credentials: Autoriser les credentials.
            allow_methods: Méthodes HTTP autorisées (None = toutes).
            allow_headers: Headers autorisés (None = tous).
        """
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
    
    async def __call__(self, scope, receive, send):
        """Gère les requêtes CORS.
        
        Args:
            scope: Scope ASGI.
            receive: Fonction receive ASGI.
            send: Fonction send ASGI.
        """
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Gérer les requêtes OPTIONS (preflight)
            if request.method == "OPTIONS":
                response = Response()
                self._add_cors_headers(response, request)
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def _add_cors_headers(self, response: Response, request: Request):
        """Ajoute les headers CORS à la réponse.
        
        Args:
            response: La réponse HTTP.
            request: La requête HTTP.
        """
        origin = request.headers.get("origin")
        
        if "*" in self.allow_origins or (origin and origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if "*" in self.allow_methods:
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        else:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        
        if "*" in self.allow_headers:
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
        else:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        response.headers["Access-Control-Max-Age"] = "3600"

