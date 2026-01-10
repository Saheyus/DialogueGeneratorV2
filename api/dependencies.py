"""Injection de dépendances pour l'API FastAPI."""
import logging
import os
import sys
import threading
import json
from pathlib import Path
from typing import Annotated
from fastapi import Depends
from starlette.requests import Request
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
from services.prompt_enricher import PromptEnricher
from services.skill_catalog_service import SkillCatalogService
from services.trait_catalog_service import TraitCatalogService
from constants import FilePaths, Defaults

logger = logging.getLogger(__name__)

# Chemins par défaut
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
# DEFAULT_INTERACTIONS_STORAGE_DIR supprimé - système obsolète

# Instances globales (singletons) pour les services qui peuvent être partagés
_context_builder: ContextBuilder | None = None
_context_builder_lock = threading.Lock()  # Verrou pour éviter les race conditions
_config_service: ConfigurationService | None = None
_prompt_engine: PromptEngine | None = None
_skill_catalog_service: SkillCatalogService | None = None
_trait_catalog_service: TraitCatalogService | None = None


def _get_config_service_singleton() -> ConfigurationService:
    """Retourne le singleton global ConfigurationService (hors contexte request)."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
        logger.info("ConfigurationService initialisé (singleton global - mode compatibilité).")
    return _config_service


def get_config_service(request: Request) -> ConfigurationService:
    """Retourne le service de configuration.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global (compatibilité).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de ConfigurationService.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    container = getattr(request.app.state, "container", None)
    if container is not None:
        return container.get_config_service()

    # Fallback vers l'ancien système (compatibilité)
    return _get_config_service_singleton()


def _get_context_builder_singleton() -> ContextBuilder:
    """Retourne le singleton global ContextBuilder (hors contexte request)."""
    global _context_builder
    if _context_builder is None:
        with _context_builder_lock:
            # Double-check après avoir acquis le lock pour éviter les initialisations multiples
            if _context_builder is None:
                # Utiliser ContextBuilderFactory pour simplifier l'initialisation
                from services.context_builder_factory import ContextBuilderFactory
                from context_builder import CONTEXT_BUILDER_DIR, PROJECT_ROOT_DIR
                _context_builder = ContextBuilderFactory.create(
                    context_builder_dir=CONTEXT_BUILDER_DIR,
                    project_root_dir=PROJECT_ROOT_DIR
                )
                logger.info("Chargement des fichiers GDD...")
                _context_builder.load_gdd_files()
                logger.info("ContextBuilder initialisé avec données GDD chargées (singleton global - mode compatibilité).")
    return _context_builder


def get_context_builder(request: Request) -> ContextBuilder:
    """Retourne le ContextBuilder.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global avec verrou (compatibilité).
    
    Le ContextBuilder charge les fichiers GDD au premier accès.
    Les chemins GDD peuvent être configurés via les variables d'environnement :
    - GDD_CATEGORIES_PATH : Chemin vers le répertoire des catégories GDD
    - GDD_IMPORT_PATH : Chemin vers le répertoire import (ou directement Bible_Narrative)
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de ContextBuilder avec données GDD chargées.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    container = getattr(request.app.state, "container", None)
    if container is not None:
        return container.get_context_builder()

    # Fallback vers l'ancien système (compatibilité)
    return _get_context_builder_singleton()


def get_prompt_engine(request: Request) -> PromptEngine:
    """Retourne le PromptEngine.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global (compatibilité).
    
    Args:
        request: La requête HTTP (optionnel, pour accéder à app.state).
        
    Returns:
        Instance de PromptEngine.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    if request is not None:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            return container.get_prompt_engine()
    
    # Fallback vers l'ancien système (compatibilité)
    global _prompt_engine
    if _prompt_engine is None:
        # Injecter ContextBuilder et services pour éviter les instanciations redondantes
        context_builder = get_context_builder(request)
        vocab_service = get_vocabulary_service(request)
        guides_service = get_narrative_guides_service(request)
        # Créer PromptEnricher avec les services injectés
        enricher = PromptEnricher(
            vocab_service=vocab_service,
            guides_service=guides_service
        )
        # Créer PromptBuilder avec les dépendances
        from services.prompt_builder import PromptBuilder
        prompt_builder = PromptBuilder(
            context_builder=context_builder,
            enricher=enricher
        )
        
        _prompt_engine = PromptEngine(
            context_builder=context_builder,
            vocab_service=vocab_service,
            guides_service=guides_service,
            enricher=enricher,
            prompt_builder=prompt_builder
        )
        logger.info("PromptEngine initialisé (singleton global - mode compatibilité) avec toutes les dépendances injectées.")
    return _prompt_engine


# get_interaction_repository supprimé - système obsolète
# get_interaction_service supprimé - système obsolète

def reset_singletons() -> None:
    """Réinitialise tous les singletons (utile lors d'un reload uvicorn).
    
    Cette fonction doit être appelée au startup du lifespan pour garantir
    que les singletons sont réinitialisés après un reload d'uvicorn.
    """
    global _context_builder, _config_service, _prompt_engine, _vocab_service, _guides_service
    global _skill_catalog_service, _trait_catalog_service
    _context_builder = None
    _config_service = None
    _prompt_engine = None
    _vocab_service = None
    _guides_service = None
    _skill_catalog_service = None
    _trait_catalog_service = None
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
    config_service = _get_config_service_singleton()
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


_vocab_service: VocabularyService | None = None
_guides_service: NarrativeGuidesService | None = None


def get_vocabulary_service(request: Request) -> VocabularyService:
    """Retourne le service de vocabulaire.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global (compatibilité).
    
    Args:
        request: La requête HTTP (optionnel, pour accéder à app.state).
        
    Returns:
        Instance de VocabularyService.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    if request is not None:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            return container.get_vocabulary_service()
    
    # Fallback vers l'ancien système (compatibilité)
    global _vocab_service
    if _vocab_service is None:
        _vocab_service = VocabularyService()
        logger.info("VocabularyService initialisé (singleton global - mode compatibilité).")
    return _vocab_service


def get_narrative_guides_service(request: Request) -> NarrativeGuidesService:
    """Retourne le service des guides narratifs.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global (compatibilité).
    
    Args:
        request: La requête HTTP (optionnel, pour accéder à app.state).
        
    Returns:
        Instance de NarrativeGuidesService.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    if request is not None:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            return container.get_narrative_guides_service()
    
    # Fallback vers l'ancien système (compatibilité)
    global _guides_service
    if _guides_service is None:
        _guides_service = NarrativeGuidesService()
        logger.info("NarrativeGuidesService initialisé (singleton global - mode compatibilité).")
    return _guides_service


def get_notion_import_service() -> NotionImportService:
    """Retourne le service d'import Notion (singleton).
    
    Returns:
        Instance de NotionImportService.
    """
    return NotionImportService()


def get_skill_catalog_service(request: Request) -> SkillCatalogService:
    """Retourne le service de catalogue des compétences.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global (compatibilité).
    
    Args:
        request: La requête HTTP (optionnel, pour accéder à app.state).
        
    Returns:
        Instance de SkillCatalogService.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    if request is not None:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            return container.get_skill_catalog_service()
    
    # Fallback vers l'ancien système (compatibilité)
    global _skill_catalog_service
    if _skill_catalog_service is None:
        _skill_catalog_service = SkillCatalogService()
        logger.info("SkillCatalogService initialisé (singleton global - mode compatibilité).")
    return _skill_catalog_service


def get_trait_catalog_service(request: Request) -> TraitCatalogService:
    """Retourne le service de catalogue des traits.
    
    Essaie d'abord d'utiliser le container dans app.state (nouveau système),
    puis fallback vers le singleton global (compatibilité).
    
    Args:
        request: La requête HTTP (optionnel, pour accéder à app.state).
        
    Returns:
        Instance de TraitCatalogService.
    """
    # Nouveau système : utiliser le container depuis app.state si disponible
    if request is not None:
        container = getattr(request.app.state, "container", None)
        if container is not None:
            return container.get_trait_catalog_service()
    
    # Fallback vers l'ancien système (compatibilité)
    global _trait_catalog_service
    if _trait_catalog_service is None:
        _trait_catalog_service = TraitCatalogService()
        logger.info("TraitCatalogService initialisé (singleton global - mode compatibilité).")
    return _trait_catalog_service

