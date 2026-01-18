"""Injection de dépendances pour l'API FastAPI.

Toutes les dépendances utilisent maintenant ServiceContainer depuis app.state.
Les singletons globaux ont été supprimés pour unifier le système d'injection.
"""
import logging
import os
import sys
import json
from pathlib import Path
from typing import Annotated
from fastapi import Depends
from starlette.requests import Request
from core.context.context_builder import ContextBuilder
from core.prompt.prompt_engine import PromptEngine
from core.llm.llm_client import ILLMClient
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
from services.preset_service import PresetService
from constants import FilePaths, Defaults

logger = logging.getLogger(__name__)

# Chemins par défaut
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
# DEFAULT_INTERACTIONS_STORAGE_DIR supprimé - système obsolète

# Les singletons globaux ont été supprimés.
# Tous les services sont maintenant gérés par ServiceContainer dans app.state.


def get_config_service(request: Request) -> ConfigurationService:
    """Retourne le service de configuration.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de ConfigurationService.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_config_service()


# _get_context_builder_singleton() supprimé - utilisez ServiceContainer via get_context_builder()


def get_context_builder(request: Request) -> ContextBuilder:
    """Retourne le ContextBuilder.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Le ContextBuilder charge les fichiers GDD au premier accès.
    Les chemins GDD peuvent être configurés via les variables d'environnement :
    - GDD_CATEGORIES_PATH : Chemin vers le répertoire des catégories GDD
    - GDD_IMPORT_PATH : Chemin vers le répertoire import (ou directement Bible_Narrative)
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de ContextBuilder avec données GDD chargées.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_context_builder()


def get_prompt_engine(request: Request) -> PromptEngine:
    """Retourne le PromptEngine.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de PromptEngine.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_prompt_engine()


# get_interaction_repository supprimé - système obsolète
# get_interaction_service supprimé - système obsolète

# reset_singletons() supprimé - le ServiceContainer gère déjà le reset via container.reset()


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
    model_identifier: str,
    request: Request
) -> ILLMClient:
    """Crée un client LLM basé sur l'identifiant du modèle.
    
    Args:
        model_identifier: Identifiant du modèle LLM à utiliser.
        request: La requête HTTP (pour accéder au container).
        
    Returns:
        Instance de ILLMClient (OpenAI ou Dummy).
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    config_service = get_config_service(request)
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


# Variables globales _vocab_service et _guides_service supprimées - utilisez ServiceContainer


def get_vocabulary_service(request: Request) -> VocabularyService:
    """Retourne le service de vocabulaire.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de VocabularyService.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_vocabulary_service()


def get_narrative_guides_service(request: Request) -> NarrativeGuidesService:
    """Retourne le service des guides narratifs.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de NarrativeGuidesService.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_narrative_guides_service()


def get_notion_import_service() -> NotionImportService:
    """Retourne le service d'import Notion (singleton).
    
    Returns:
        Instance de NotionImportService.
    """
    return NotionImportService()


def get_skill_catalog_service(request: Request) -> SkillCatalogService:
    """Retourne le service de catalogue des compétences.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de SkillCatalogService.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_skill_catalog_service()


def get_trait_catalog_service(request: Request) -> TraitCatalogService:
    """Retourne le service de catalogue des traits.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de TraitCatalogService.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_trait_catalog_service()


def get_preset_service(request: Request) -> PresetService:
    """Retourne le service de gestion des presets.
    
    Utilise le ServiceContainer depuis app.state (système unifié).
    
    Args:
        request: La requête HTTP (injecté automatiquement par FastAPI).
        
    Returns:
        Instance de PresetService.
        
    Raises:
        RuntimeError: Si le ServiceContainer n'est pas initialisé dans app.state.
    """
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise RuntimeError("ServiceContainer not initialized in app.state. Ensure app.state.container is set in lifespan.")
    return container.get_preset_service()

