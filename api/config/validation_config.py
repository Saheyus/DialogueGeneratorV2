"""Configuration pour la validation des exports Unity."""
import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

from api.config.security_config import SecurityConfig

logger = logging.getLogger(__name__)


class ValidationConfig(BaseSettings):
    """Configuration pour la validation des exports Unity.
    
    Charge les variables d'environnement depuis .env ou les variables d'environnement système.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Unity Schema Validation
    enable_unity_schema_validation: bool = False
    
    def should_validate_unity_schema(self, security_config: SecurityConfig) -> bool:
        """Détermine si la validation Unity Schema doit être activée.
        
        Args:
            security_config: Configuration de sécurité pour vérifier l'environnement.
            
        Returns:
            True si la validation doit être activée, False sinon.
            
        Conditions:
            - Le flag ENABLE_UNITY_SCHEMA_VALIDATION doit être True
            - L'environnement ne doit pas être production
            - Le schéma doit être disponible (vérifié via api.utils.unity_schema_validator)
        """
        if not self.enable_unity_schema_validation:
            return False
        
        if security_config.is_production:
            logger.debug("Validation Unity Schema désactivée en production")
            return False
        
        # Vérifier que le schéma existe
        from api.utils.unity_schema_validator import schema_exists
        if not schema_exists():
            logger.debug("Schéma Unity non disponible, validation désactivée")
            return False
        
        return True


# Instance globale (sera initialisée au démarrage de l'API)
_validation_config: ValidationConfig | None = None


def get_validation_config() -> ValidationConfig:
    """Récupère l'instance globale de ValidationConfig.
    
    Returns:
        L'instance de ValidationConfig.
    """
    global _validation_config
    if _validation_config is None:
        _validation_config = ValidationConfig()
    return _validation_config

