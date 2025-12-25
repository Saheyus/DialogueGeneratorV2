"""Injection de dépendances pour l'API FastAPI."""
import logging
import os
from pathlib import Path
from typing import Annotated
from fastapi import Depends, Request
from context_builder import ContextBuilder
from prompt_engine import PromptEngine
from llm_client import ILLMClient
from services.configuration_service import ConfigurationService
from services.interaction_service import InteractionService
from services.dialogue_generation_service import DialogueGenerationService
from services.repositories.file_repository import FileInteractionRepository
from factories.llm_factory import LLMClientFactory
from constants import FilePaths, Defaults

logger = logging.getLogger(__name__)

# Chemins par défaut
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INTERACTIONS_STORAGE_DIR = DIALOGUE_GENERATOR_DIR / FilePaths.INTERACTIONS_DIR


# Instances globales (singletons) pour les services qui peuvent être partagés
_context_builder: ContextBuilder | None = None
_config_service: ConfigurationService | None = None
_prompt_engine: PromptEngine | None = None


def get_config_service() -> ConfigurationService:
    """Retourne le service de configuration (singleton).
    
    Returns:
        Instance de ConfigurationService.
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
        logger.info("ConfigurationService initialisé (singleton).")
    return _config_service


def get_context_builder() -> ContextBuilder:
    """Retourne le ContextBuilder (singleton).
    
    Le ContextBuilder charge les fichiers GDD au premier accès.
    
    Returns:
        Instance de ContextBuilder avec données GDD chargées.
    """
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
        logger.info("Chargement des fichiers GDD...")
        _context_builder.load_gdd_files()
        logger.info("ContextBuilder initialisé avec données GDD chargées (singleton).")
    return _context_builder


def get_prompt_engine() -> PromptEngine:
    """Retourne le PromptEngine (singleton).
    
    Returns:
        Instance de PromptEngine.
    """
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
        logger.info("PromptEngine initialisé (singleton).")
    return _prompt_engine


def get_interaction_repository() -> FileInteractionRepository:
    """Crée un repository d'interactions basé sur fichiers.
    
    Returns:
        Instance de FileInteractionRepository.
    """
    storage_dir = str(DEFAULT_INTERACTIONS_STORAGE_DIR)
    os.makedirs(storage_dir, exist_ok=True)
    return FileInteractionRepository(storage_dir=storage_dir)


def get_interaction_service(
    repository: Annotated[FileInteractionRepository, Depends(get_interaction_repository)]
) -> InteractionService:
    """Retourne le service d'interactions.
    
    Args:
        repository: Repository injecté via dépendance.
        
    Returns:
        Instance de InteractionService.
    """
    return InteractionService(repository=repository)


def get_dialogue_generation_service(
    context_builder: Annotated[ContextBuilder, Depends(get_context_builder)],
    prompt_engine: Annotated[PromptEngine, Depends(get_prompt_engine)],
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)]
) -> DialogueGenerationService:
    """Retourne le service de génération de dialogues.
    
    Args:
        context_builder: ContextBuilder injecté.
        prompt_engine: PromptEngine injecté.
        interaction_service: InteractionService injecté.
        
    Returns:
        Instance de DialogueGenerationService.
    """
    return DialogueGenerationService(
        context_builder=context_builder,
        prompt_engine=prompt_engine,
        interaction_service=interaction_service
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


def get_request_id(request: Request) -> str:
    """Extrait le request_id de la requête.
    
    Args:
        request: La requête HTTP.
        
    Returns:
        Le request_id ou "unknown" si absent.
    """
    return getattr(request.state, "request_id", "unknown")

