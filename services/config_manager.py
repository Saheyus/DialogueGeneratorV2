"""Gestionnaire centralisé de configuration utilisant Pydantic Settings.

Ce module centralise toutes les configurations de l'application :
- Variables d'environnement (via Pydantic Settings)
- Fichiers de configuration JSON (via ConfigurationService)
- Validation et typage automatiques
"""
import logging
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppConfig(BaseSettings):
    """Configuration principale de l'application.
    
    Centralise toutes les variables d'environnement avec validation et typage.
    Utilise Pydantic Settings pour le chargement depuis .env et variables d'environnement.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Chemins GDD
    gdd_categories_path: Optional[str] = None
    gdd_import_path: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Environnement
    environment: str = "development"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    @property
    def is_production(self) -> bool:
        """Indique si l'application est en mode production.
        
        Returns:
            True si ENVIRONMENT=production, False sinon.
        """
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Indique si l'application est en mode développement.
        
        Returns:
            True si ENVIRONMENT=development, False sinon.
        """
        return self.environment.lower() == "development"
    
    def get_gdd_categories_path(self) -> Optional[Path]:
        """Retourne le chemin des catégories GDD en tant que Path.
        
        Returns:
            Path vers les catégories GDD ou None.
        """
        if self.gdd_categories_path:
            return Path(self.gdd_categories_path)
        return None
    
    def get_gdd_import_path(self) -> Optional[Path]:
        """Retourne le chemin d'import GDD en tant que Path.
        
        Returns:
            Path vers le répertoire import ou None.
        """
        if self.gdd_import_path:
            return Path(self.gdd_import_path)
        return None
    
    def get_cors_origins_list(self) -> list[str]:
        """Retourne la liste des origines CORS.
        
        Returns:
            Liste des origines CORS (séparées par virgule).
        """
        if not self.cors_origins:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


class ConfigManager:
    """Gestionnaire centralisé de configuration.
    
    Fournit un point d'accès unique à toutes les configurations :
    - Variables d'environnement (via AppConfig)
    - Fichiers de configuration JSON (via ConfigurationService)
    
    Pattern Singleton pour garantir une seule instance.
    """
    
    _instance: Optional['ConfigManager'] = None
    _app_config: Optional[AppConfig] = None
    
    def __new__(cls):
        """Implémente le pattern Singleton.
        
        Returns:
            Instance unique de ConfigManager.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialise le ConfigManager (appelé une seule fois grâce au Singleton)."""
        if self._app_config is None:
            self._app_config = AppConfig()
            logger.info("ConfigManager initialisé avec AppConfig")
    
    @property
    def app_config(self) -> AppConfig:
        """Retourne la configuration de l'application.
        
        Returns:
            Instance de AppConfig.
        """
        return self._app_config
    
    def get_gdd_categories_path(self) -> Optional[Path]:
        """Retourne le chemin des catégories GDD.
        
        Returns:
            Path vers les catégories GDD ou None.
        """
        return self._app_config.get_gdd_categories_path()
    
    def get_gdd_import_path(self) -> Optional[Path]:
        """Retourne le chemin d'import GDD.
        
        Returns:
            Path vers le répertoire import ou None.
        """
        return self._app_config.get_gdd_import_path()
    
    def get_openai_api_key(self) -> Optional[str]:
        """Retourne la clé API OpenAI.
        
        Returns:
            Clé API OpenAI ou None.
        """
        return self._app_config.openai_api_key
    
    def get_environment(self) -> str:
        """Retourne l'environnement (development/production).
        
        Returns:
            Environnement de l'application.
        """
        return self._app_config.environment
    
    def is_production(self) -> bool:
        """Indique si l'application est en mode production.
        
        Returns:
            True si en production, False sinon.
        """
        return self._app_config.is_production
    
    def is_development(self) -> bool:
        """Indique si l'application est en mode développement.
        
        Returns:
            True si en développement, False sinon.
        """
        return self._app_config.is_development
    
    def get_cors_origins(self) -> list[str]:
        """Retourne la liste des origines CORS.
        
        Returns:
            Liste des origines CORS.
        """
        return self._app_config.get_cors_origins_list()


# Instance globale (singleton)
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Retourne l'instance unique de ConfigManager.
    
    Returns:
        Instance de ConfigManager (singleton).
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
