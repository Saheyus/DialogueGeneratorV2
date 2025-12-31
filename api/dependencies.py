"""Injection de dépendances pour l'API FastAPI."""
import logging
import os
import sys
import threading
import json
from pathlib import Path
from typing import Annotated
from fastapi import Depends, Request
from context_builder import ContextBuilder
from prompt_engine import PromptEngine
from llm_client import ILLMClient
from services.configuration_service import ConfigurationService
# InteractionService supprimé - système obsolète
from services.dialogue_generation_service import DialogueGenerationService
from services.linked_selector import LinkedSelectorService
# FileInteractionRepository supprimé - système obsolète
from services.repositories.llm_usage_repository import FileLLMUsageRepository
from services.llm_usage_service import LLMUsageService
from services.llm_pricing_service import LLMPricingService
from factories.llm_factory import LLMClientFactory
from services.vocabulary_service import VocabularyService
from services.narrative_guides_service import NarrativeGuidesService
from services.notion_import_service import NotionImportService
from constants import FilePaths, Defaults

logger = logging.getLogger(__name__)

# Chemins par défaut
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
# DEFAULT_INTERACTIONS_STORAGE_DIR supprimé - système obsolète

# #region agent log
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str = None):
    """Log de debug pour instrumentation."""
    try:
        log_path = Path(__file__).parent.parent / ".cursor" / "debug.log"
        log_entry = {
            "id": f"log_{int(__import__('time').time() * 1000)}",
            "timestamp": int(__import__('time').time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
# #endregion

# Instances globales (singletons) pour les services qui peuvent être partagés
_context_builder: ContextBuilder | None = None
_context_builder_lock = threading.Lock()  # Verrou pour éviter les race conditions
_config_service: ConfigurationService | None = None
_prompt_engine: PromptEngine | None = None

# #region agent log
# Log au chargement du module pour vérifier si le module est rechargé
_module_id = id(sys.modules[__name__])
_debug_log(
    "api/dependencies.py:37",
    "Module dependencies.py chargé",
    {
        "module_id": _module_id,
        "module_name": __name__,
        "_context_builder_id": id(_context_builder) if _context_builder is not None else None,
        "_config_service_id": id(_config_service) if _config_service is not None else None,
        "_prompt_engine_id": id(_prompt_engine) if _prompt_engine is not None else None,
        "in_sys_modules": __name__ in sys.modules,
        "sys_modules_id": id(sys.modules.get(__name__))
    },
    "A"
)
# #endregion


def get_config_service() -> ConfigurationService:
    """Retourne le service de configuration (singleton).
    
    Returns:
        Instance de ConfigurationService.
    """
    global _config_service
    # #region agent log
    _debug_log(
        "api/dependencies.py:get_config_service:entry",
        "get_config_service appelé",
        {
            "_config_service_is_none": _config_service is None,
            "_config_service_id": id(_config_service) if _config_service is not None else None,
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    if _config_service is None:
        _config_service = ConfigurationService()
        # #region agent log
        _debug_log(
            "api/dependencies.py:get_config_service:created",
            "ConfigurationService créé",
            {
                "new_service_id": id(_config_service),
                "module_id": id(sys.modules[__name__])
            },
            "A"
        )
        # #endregion
        logger.info("ConfigurationService initialisé (singleton).")
    # #region agent log
    _debug_log(
        "api/dependencies.py:get_config_service:exit",
        "get_config_service retourne",
        {
            "returned_service_id": id(_config_service),
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    return _config_service


def get_context_builder() -> ContextBuilder:
    """Retourne le ContextBuilder (singleton).
    
    Le ContextBuilder charge les fichiers GDD au premier accès.
    Utilise un verrou pour éviter les race conditions lors d'appels simultanés.
    Les chemins GDD peuvent être configurés via les variables d'environnement :
    - GDD_CATEGORIES_PATH : Chemin vers le répertoire des catégories GDD
    - GDD_IMPORT_PATH : Chemin vers le répertoire import (ou directement Bible_Narrative)
    
    Returns:
        Instance de ContextBuilder avec données GDD chargées.
    """
    global _context_builder
    # #region agent log
    _debug_log(
        "api/dependencies.py:get_context_builder:entry",
        "get_context_builder appelé",
        {
            "_context_builder_is_none": _context_builder is None,
            "_context_builder_id": id(_context_builder) if _context_builder is not None else None,
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    if _context_builder is None:
        with _context_builder_lock:
            # Double-check après avoir acquis le lock pour éviter les initialisations multiples
            if _context_builder is None:
                # Les chemins sont maintenant lus depuis les variables d'environnement
                # dans le constructeur de ContextBuilder
                _context_builder = ContextBuilder()
                # #region agent log
                _debug_log(
                    "api/dependencies.py:get_context_builder:created",
                    "ContextBuilder créé",
                    {
                        "new_builder_id": id(_context_builder),
                        "module_id": id(sys.modules[__name__])
                    },
                    "A"
                )
                # #endregion
                logger.info("Chargement des fichiers GDD...")
                _context_builder.load_gdd_files()
                logger.info("ContextBuilder initialisé avec données GDD chargées (singleton).")
    # #region agent log
    _debug_log(
        "api/dependencies.py:get_context_builder:exit",
        "get_context_builder retourne",
        {
            "returned_builder_id": id(_context_builder),
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    return _context_builder


def get_prompt_engine() -> PromptEngine:
    """Retourne le PromptEngine (singleton).
    
    Returns:
        Instance de PromptEngine.
    """
    global _prompt_engine
    # #region agent log
    _debug_log(
        "api/dependencies.py:get_prompt_engine:entry",
        "get_prompt_engine appelé",
        {
            "_prompt_engine_is_none": _prompt_engine is None,
            "_prompt_engine_id": id(_prompt_engine) if _prompt_engine is not None else None,
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
        # #region agent log
        _debug_log(
            "api/dependencies.py:get_prompt_engine:created",
            "PromptEngine créé",
            {
                "new_engine_id": id(_prompt_engine),
                "module_id": id(sys.modules[__name__])
            },
            "A"
        )
        # #endregion
        logger.info("PromptEngine initialisé (singleton).")
    # #region agent log
    _debug_log(
        "api/dependencies.py:get_prompt_engine:exit",
        "get_prompt_engine retourne",
        {
            "returned_engine_id": id(_prompt_engine),
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    return _prompt_engine


# get_interaction_repository supprimé - système obsolète
# get_interaction_service supprimé - système obsolète

def reset_singletons() -> None:
    """Réinitialise tous les singletons (utile lors d'un reload uvicorn).
    
    Cette fonction doit être appelée au startup du lifespan pour garantir
    que les singletons sont réinitialisés après un reload d'uvicorn.
    """
    global _context_builder, _config_service, _prompt_engine
    # #region agent log
    _debug_log(
        "api/dependencies.py:reset_singletons:entry",
        "Réinitialisation des singletons",
        {
            "_context_builder_id_before": id(_context_builder) if _context_builder is not None else None,
            "_config_service_id_before": id(_config_service) if _config_service is not None else None,
            "_prompt_engine_id_before": id(_prompt_engine) if _prompt_engine is not None else None,
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    _context_builder = None
    _config_service = None
    _prompt_engine = None
    # #region agent log
    _debug_log(
        "api/dependencies.py:reset_singletons:exit",
        "Singletons réinitialisés",
        {
            "_context_builder_id_after": id(_context_builder) if _context_builder is not None else None,
            "_config_service_id_after": id(_config_service) if _config_service is not None else None,
            "_prompt_engine_id_after": id(_prompt_engine) if _prompt_engine is not None else None,
            "module_id": id(sys.modules[__name__])
        },
        "A"
    )
    # #endregion
    logger.info("Singletons réinitialisés (reload détecté).")


def get_dialogue_generation_service(
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    prompt_engine: Annotated[PromptEngine, Depends(get_prompt_engine)]
) -> DialogueGenerationService:
    """Retourne le service de génération de dialogues.
    
    Args:
        context_builder: ContextBuilder injecté.
        prompt_engine: PromptEngine injecté.
        
    Returns:
        Instance de DialogueGenerationService.
    """
    return DialogueGenerationService(
        context_builder=context_builder,
        prompt_engine=prompt_engine
    )


def get_llm_client(
    model_identifier: str
) -> ILLMClient:
    """Crée un client LLM basé sur l'identifiant du modèle.
    
    Args:
        model_identifier: Identifiant du modèle LLM à utiliser.
        
    Returns:
        Instance de ILLMClient (OpenAI ou Dummy).
    """
    config_service = get_config_service()
    llm_config = config_service.get_llm_config()
    available_models = config_service.get_available_llm_models()
    
    return LLMClientFactory.create_client(
        model_id=model_identifier,
        config=llm_config,
        available_models=available_models
    )


def get_linked_selector_service(
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)]
) -> LinkedSelectorService:
    """Retourne le service de sélection d'éléments liés.
    
    Args:
        context_builder: ContextBuilder injecté.
        
    Returns:
        Instance de LinkedSelectorService.
    """
    return LinkedSelectorService(context_builder=context_builder)


def get_llm_usage_repository() -> FileLLMUsageRepository:
    """Crée un repository d'utilisation LLM basé sur fichiers.
    
    Returns:
        Instance de FileLLMUsageRepository.
    """
    storage_dir = str(DIALOGUE_GENERATOR_DIR / FilePaths.LLM_USAGE_DIR)
    os.makedirs(storage_dir, exist_ok=True)
    return FileLLMUsageRepository(storage_dir=storage_dir)


def create_llm_usage_service() -> LLMUsageService:
    """Crée un service de tracking d'utilisation LLM (sans dépendances FastAPI).
    
    Cette fonction peut être appelée directement sans passer par le système
    de dépendances FastAPI. Pour l'injection de dépendances dans les routes,
    utiliser get_llm_usage_service() avec Depends().
    
    Returns:
        Instance de LLMUsageService.
    """
    repository = get_llm_usage_repository()
    return LLMUsageService(repository=repository)


def get_llm_usage_service(
    repository: Annotated[FileLLMUsageRepository, Depends(get_llm_usage_repository)]
) -> LLMUsageService:
    """Retourne le service de tracking d'utilisation LLM.
    
    Args:
        repository: Repository injecté via dépendance.
        
    Returns:
        Instance de LLMUsageService.
    """
    return LLMUsageService(repository=repository)


def get_request_id(request: Request) -> str:
    """Extrait le request_id de la requête.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        Le request_id ou "unknown" si absent.
    """
    return getattr(request.state, "request_id", "unknown")


def get_vocabulary_service() -> VocabularyService:
    """Retourne le service de vocabulaire (singleton).
    
    Returns:
        Instance de VocabularyService.
    """
    return VocabularyService()


def get_narrative_guides_service() -> NarrativeGuidesService:
    """Retourne le service des guides narratifs (singleton).
    
    Returns:
        Instance de NarrativeGuidesService.
    """
    return NarrativeGuidesService()


def get_notion_import_service() -> NotionImportService:
    """Retourne le service d'import Notion (singleton).
    
    Returns:
        Instance de NotionImportService.
    """
    return NotionImportService()

