"""Point d'entrée principal de l'API REST FastAPI."""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.responses import JSONResponse
from api.middleware import RequestIDMiddleware, LoggingMiddleware
from api.exceptions import APIException, ValidationException
from api.dependencies import get_request_id

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
cors_origins_env = os.getenv("CORS_ORIGINS", "")
is_production_env = os.getenv("ENVIRONMENT", "development") == "production"

# En production, lire depuis CORS_ORIGINS (format CSV), sinon permettre tout en dev
if is_production_env and cors_origins_env:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    cors_origins = ["*"]  # Dev par défaut

app.add_middleware(
    FastAPICORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware personnalisés
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)


# Handler pour les erreurs de validation FastAPI/Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Gère les erreurs de validation FastAPI/Pydantic.
    
    Transforme le format natif FastAPI en format API standardisé.
    
    Args:
        request: La requête HTTP.
        exc: L'exception de validation.
        
    Returns:
        Réponse JSON avec format d'erreur standardisé.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Transformer les erreurs Pydantic en format simple : {champ: message}
    errors = exc.errors()
    details = {}
    for err in errors:
        # err["loc"] est une liste comme ("body", "field_name") ou ("query", "param")
        # On prend le dernier élément comme nom de champ
        field_path = ".".join(str(loc) for loc in err["loc"] if loc != "body" and loc != "query")
        if not field_path:
            field_path = ".".join(str(loc) for loc in err["loc"])
        details[field_path] = err["msg"]
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Erreur de validation des données",
                "details": details,
                "request_id": request_id
            }
        }
    )


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

# Servir le frontend statique en production (APRÈS les routes API)
if is_production_env:
    try:
        from fastapi.staticfiles import StaticFiles
        from pathlib import Path
        
        # Chemin vers le dossier dist du frontend
        frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
        
        if frontend_dist.exists():
            app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
            logger.info(f"Frontend statique monté depuis: {frontend_dist}")
        else:
            logger.warning(f"Dossier frontend/dist introuvable: {frontend_dist}")
    except ImportError:
        logger.warning("StaticFiles non disponible, le frontend ne sera pas servi")
    except Exception as e:
        logger.error(f"Erreur lors du montage du frontend statique: {e}")


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import time
    
    def open_browser():
        """Ouvre le navigateur après un court délai pour laisser le serveur démarrer."""
        time.sleep(1.5)  # Attendre que le serveur démarre
        port = int(os.getenv("API_PORT", "4242"))
        webbrowser.open(f"http://localhost:{port}/api/docs")
    
    # Lancer l'ouverture du navigateur dans un thread séparé
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "4242")),
        reload=True,
        log_level="info"
    )

