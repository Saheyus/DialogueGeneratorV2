"""Configuration du logging structuré pour l'API."""
import os
import sys
import logging
import json
from typing import Any, Dict
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Formateur JSON pour les logs structurés.
    
    Convertit les logs en format JSON pour faciliter l'analyse avec
    des outils comme ELK, CloudWatch, etc.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un log record en JSON.
        
        Args:
            record: Le record de log à formater.
            
        Returns:
            Chaîne JSON formatée.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Ajouter le contexte enrichi si présent
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "environment"):
            log_data["environment"] = record.environment
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        
        # Ajouter les extra fields si présents
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """Formateur structuré lisible pour le développement.
    
    Format texte lisible avec contexte enrichi.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un log record en texte structuré.
        
        Args:
            record: Le record de log à formater.
            
        Returns:
            Chaîne formatée avec contexte.
        """
        parts = [
            f"[{record.levelname:8s}]",
            f"{record.name}:{record.funcName}:{record.lineno}"
        ]
        
        # Ajouter le contexte enrichi
        context_parts = []
        if hasattr(record, "request_id"):
            context_parts.append(f"request_id={record.request_id}")
        if hasattr(record, "user_id"):
            context_parts.append(f"user_id={record.user_id}")
        if hasattr(record, "endpoint"):
            context_parts.append(f"endpoint={record.method} {record.endpoint}")
        if hasattr(record, "status_code"):
            context_parts.append(f"status={record.status_code}")
        if hasattr(record, "duration_ms"):
            context_parts.append(f"duration={record.duration_ms}ms")
        
        if context_parts:
            parts.append(f"({', '.join(context_parts)})")
        
        parts.append(record.getMessage())
        
        # Ajouter l'exception si présente
        if record.exc_info:
            parts.append("\n" + self.formatException(record.exc_info))
        
        return " ".join(parts)


def get_log_format() -> str:
    """Retourne le format de log configuré.
    
    Returns:
        Format de log : "json" ou "text".
    """
    format_str = os.getenv("LOG_FORMAT", "").lower()
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    # Par défaut : text en dev, json en prod
    if not format_str:
        return "json" if environment == "production" else "text"
    
    return format_str if format_str in ("json", "text") else "text"


def get_log_level() -> str:
    """Retourne le niveau de log configuré.
    
    Returns:
        Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    return level if level in valid_levels else "INFO"


def setup_logging() -> None:
    """Configure le logging structuré pour l'API.
    
    Configure le format (JSON ou text) selon l'environnement et les variables
    d'environnement.
    """
    log_format = get_log_format()
    log_level = get_log_level()
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Créer le formateur approprié
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter(
            fmt="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Configurer le handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Configurer le root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers = []  # Nettoyer les handlers existants
    root_logger.addHandler(console_handler)
    
    # Réduire la verbosité de certains loggers spécifiques
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sentry_sdk").setLevel(logging.WARNING)
    # Réduire la verbosité des logs watchfiles (reload automatique)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main._log_changes").setLevel(logging.WARNING)
    # Réduire la verbosité des logs du cache HTTP et GDD en développement
    if log_format == "text":  # En développement (format texte)
        logging.getLogger("api.middleware.http_cache").setLevel(logging.INFO)
        logging.getLogger("api.utils.gdd_cache").setLevel(logging.INFO)
        # Réduire aussi les logs DEBUG du context_builder en développement
        logging.getLogger("context_builder").setLevel(logging.INFO)
    
    # Ajouter l'environnement au logger context
    # (sera enrichi par le middleware)
    logging.LoggerAdapter(logging.getLogger("api"), {"environment": environment})
    
    # Logger la configuration
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configuré: format={log_format}, level={log_level}, environment={environment}",
        extra={"environment": environment}
    )



