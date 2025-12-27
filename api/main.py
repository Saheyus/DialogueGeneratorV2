"""Point d'entrée principal de l'API REST FastAPI."""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from api.middleware import RequestIDMiddleware, LoggingMiddleware
from api.exceptions import APIException, ValidationException
from api.dependencies import get_request_id
from api.config.security_config import get_security_config
from api.middleware.rate_limiter import get_limiter, rate_limit_exception_handler

# Configuration du logging structuré
from api.utils.logging_config import setup_logging
setup_logging()

# Initialiser Sentry si configuré (doit être fait après le logging)
from api.utils.sentry_config import init_sentry
init_sentry()

logger = logging.getLogger(__name__)

# Créer le limiter global (peut être None si désactivé)
limiter = get_limiter()


def _validate_security_config() -> None:
    """Valide la configuration de sécurité au démarrage.
    
    Raises:
        ValueError: Si la configuration est invalide en production.
    """
    try:
        security_config = get_security_config()
        security_config.validate_config()
        # Validation réussie (pas de log nécessaire, seulement les erreurs sont loggées)
    except ValueError as e:
        logger.critical(f"Configuration de sécurité invalide: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application (startup/shutdown).
    
    Args:
        app: L'application FastAPI.
    """
    # Startup
    logger.info("Démarrage de l'API DialogueGenerator...")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    
    # Valider la configuration de sécurité
    try:
        _validate_security_config()
    except ValueError:
        logger.critical("L'application ne peut pas démarrer avec une configuration de sécurité invalide.")
        raise
    
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

# Attacher le limiter à l'app si activé (requis pour que slowapi fonctionne)
if limiter is not None:
    app.state.limiter = limiter

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

# Middleware de cache HTTP (doit être après RequestID et Logging pour avoir les headers)
from api.middleware.http_cache import setup_http_cache
setup_http_cache(app)

# Métriques Prometheus (optionnel)
from api.utils.metrics import setup_prometheus_metrics
prometheus_instrumentator = setup_prometheus_metrics(app)


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


# Handler pour les erreurs de rate limiting (seulement si le limiter est activé)
if limiter is not None:
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        """Gère les erreurs de rate limiting.
        
        Args:
            request: La requête HTTP.
            exc: L'exception RateLimitExceeded.
            
        Returns:
            Réponse JSON avec erreur 429.
        """
        return await rate_limit_exception_handler(request, exc)


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
async def health_check() -> JSONResponse:
    """Endpoint de vérification de santé basique de l'API.
    
    Returns:
        Statut de santé basique de l'API (200 si healthy, 503 si unhealthy).
    """
    from api.utils.health_check import perform_health_checks
    
    health_result = perform_health_checks(detailed=False)
    health_result["timestamp"] = datetime.utcnow().isoformat() + "Z"
    health_result["service"] = "DialogueGenerator API"
    
    # Retourner 503 si unhealthy
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE if health_result["status"] == "unhealthy" else status.HTTP_200_OK
    
    return JSONResponse(
        status_code=status_code,
        content=health_result
    )


@app.get("/health/detailed", tags=["Health"])
async def health_check_detailed() -> JSONResponse:
    """Endpoint de vérification de santé détaillé avec toutes les dépendances.
    
    Returns:
        Statut de santé détaillé avec vérification de toutes les dépendances (200 si healthy, 503 si unhealthy).
    """
    from api.utils.health_check import perform_health_checks
    
    health_result = perform_health_checks(detailed=True)
    health_result["timestamp"] = datetime.utcnow().isoformat() + "Z"
    health_result["service"] = "DialogueGenerator API"
    
    # Retourner 503 si unhealthy, 200 même si degraded (l'app fonctionne mais avec limitations)
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE if health_result["status"] == "unhealthy" else status.HTTP_200_OK
    
    return JSONResponse(
        status_code=status_code,
        content=health_result
    )


# Inclusion des routers
from api.routers import auth, dialogues, interactions, context, config, llm_usage

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dialogues.router, prefix="/api/v1/dialogues", tags=["Dialogues"])
app.include_router(interactions.router, prefix="/api/v1/interactions", tags=["Interactions"])
app.include_router(context.router, prefix="/api/v1/context", tags=["Context"])
app.include_router(config.router, prefix="/api/v1/config", tags=["Configuration"])
app.include_router(llm_usage.router, prefix="/api/v1/llm-usage", tags=["LLM Usage"])

# Routers pour vocabulaire et guides narratifs
from api.routers import vocabulary, narrative_guides
app.include_router(vocabulary.router)
app.include_router(narrative_guides.router)

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
    from pathlib import Path
    
    # ⚠️ AVERTISSEMENT : Pour le développement, utiliser 'npm run dev' à la racine du projet
    # Ce script lance uniquement le backend. Pour lancer backend + frontend ensemble, utiliser 'npm run dev'
    # L'ouverture automatique du navigateur est désactivée
    # Le script dev.js gère l'ouverture du navigateur pour le frontend
    
    # Désactiver le reload automatique si RELOAD=false dans l'environnement
    # Par défaut, reload=True en développement pour recharger automatiquement
    enable_reload = os.getenv("RELOAD", "true").lower() not in ("false", "0", "no", "off")
    
    # Configuration du reload pour éviter les redémarrages trop fréquents
    reload_config = {}
    if enable_reload:
        # Limiter la surveillance aux dossiers pertinents (évite les redémarrages
        # lors de modifications dans frontend/, tests/, docs/, etc.)
        project_root = Path(__file__).parent.parent
        reload_dirs = [
            str(project_root / "api"),
            str(project_root / "services"),
            str(project_root / "core"),
            str(project_root / "domain"),
        ]
        # Vérifier que les dossiers existent
        reload_dirs = [d for d in reload_dirs if Path(d).exists()]
        
        reload_config = {
            "reload": True,
            "reload_dirs": reload_dirs,
            "reload_delay": 1.0,  # Délai de 1 seconde pour éviter les redémarrages trop fréquents
        }
    else:
        reload_config = {"reload": False}
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "4242")),
        log_level="info",
        **reload_config
    )

