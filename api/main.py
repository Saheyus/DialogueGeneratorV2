"""Point d'entrée principal de l'API REST FastAPI."""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.responses import JSONResponse
from api.middleware import RequestIDMiddleware, LoggingMiddleware
from api.exceptions import APIException

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown).
    
    Args:
        app: L'application FastAPI.
    """
    # Startup
    logger.info("Démarrage de l'API DialogueGenerator...")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    yield
    # Shutdown
    logger.info("Arrêt de l'API DialogueGenerator...")


# Création de l'application FastAPI
app = FastAPI(
    title="DialogueGenerator API",
    description="API REST pour la génération de dialogues IA pour jeux de rôle",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    FastAPICORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware personnalisés
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)


# Handler global d'exceptions
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Gère les exceptions API personnalisées.
    
    Args:
        request: La requête HTTP.
        exc: L'exception API.
        
    Returns:
        Réponse JSON avec format d'erreur standardisé.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "details": exc.details,
                "request_id": exc.request_id or request_id
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Gère les exceptions non gérées.
    
    Args:
        request: La requête HTTP.
        exc: L'exception.
        
    Returns:
        Réponse JSON avec erreur générique (détails non exposés en production).
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(f"Exception non gérée (request_id: {request_id}): {exc}")
    
    # En production, ne pas exposer les détails de l'exception
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Une erreur interne s'est produite",
                "details": {} if is_production else {"type": type(exc).__name__, "message": str(exc)},
                "request_id": request_id
            }
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Endpoint de vérification de santé de l'API.
    
    Returns:
        Statut de santé de l'API.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "DialogueGenerator API"
    }


# Inclusion des routers
from api.routers import auth, dialogues, interactions, context, config

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dialogues.router, prefix="/api/v1/dialogues", tags=["Dialogues"])
app.include_router(interactions.router, prefix="/api/v1/interactions", tags=["Interactions"])
app.include_router(context.router, prefix="/api/v1/context", tags=["Context"])
app.include_router(config.router, prefix="/api/v1/config", tags=["Configuration"])


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import time
    
    def open_browser():
        """Ouvre le navigateur après un court délai pour laisser le serveur démarrer."""
        time.sleep(1.5)  # Attendre que le serveur démarre
        webbrowser.open("http://localhost:8000/api/docs")
    
    # Lancer l'ouverture du navigateur dans un thread séparé
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

