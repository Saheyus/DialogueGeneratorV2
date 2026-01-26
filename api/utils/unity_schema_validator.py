"""Validateur de schéma JSON Unity pour les dialogues.

Ce module charge et valide les exports Unity contre le schéma JSON Schema
fourni par Unity. Le schéma est chargé depuis docs/resources/ et n'est
disponible qu'en développement (pas en production).

Si le schéma est absent, les fonctions retournent des valeurs par défaut
sans erreur (graceful degradation).
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Chemin relatif depuis la racine du projet
_SCHEMA_PATH = Path(__file__).parent.parent.parent / "docs" / "resources" / "dialogue-format.schema.json"

# Cache du schéma chargé
_schema_cache: Optional[Dict[str, Any]] = None


def load_unity_schema() -> Optional[Dict[str, Any]]:
    """Charge le schéma JSON Unity depuis le fichier.
    
    Returns:
        Le schéma JSON sous forme de dict, ou None si le fichier est absent.
        
    Note:
        Le schéma est mis en cache après le premier chargement.
    """
    global _schema_cache
    
    if _schema_cache is not None:
        return _schema_cache
    
    if not _SCHEMA_PATH.exists():
        logger.debug(f"Schéma Unity non trouvé à {_SCHEMA_PATH} (normal en production)")
        return None
    
    try:
        with open(_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            _schema_cache = json.load(f)
        logger.info(f"Schéma Unity chargé depuis {_SCHEMA_PATH}")
        return _schema_cache
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Erreur lors du chargement du schéma Unity: {e}")
        return None


def validate_unity_json(json_data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Valide un JSON Unity contre le schéma.
    
    Args:
        json_data: Liste de dictionnaires représentant les nœuds Unity.
        
    Returns:
        Tuple (is_valid, errors) où errors est la liste des messages d'erreur.
        Si le schéma est absent, retourne (True, []) (graceful degradation).
    """
    schema = load_unity_schema()
    
    if schema is None:
        # Schéma absent : pas d'erreur, juste pas de validation
        return (True, [])
    
    try:
        import jsonschema
        from jsonschema import ValidationError
        
        validator = jsonschema.Draft7Validator(schema)
        errors = []
        
        for error in validator.iter_errors(json_data):
            # Formater l'erreur de manière lisible
            path = " -> ".join(str(p) for p in error.path)
            error_msg = f"{error.message}"
            if path:
                error_msg = f"[{path}] {error_msg}"
            errors.append(error_msg)
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(f"Validation Unity échouée: {len(errors)} erreur(s)")
            for error in errors[:5]:  # Logger les 5 premières erreurs
                logger.warning(f"  - {error}")
        
        return (is_valid, errors)
        
    except ImportError:
        logger.warning("jsonschema non installé, validation Unity désactivée")
        return (True, [])
    except Exception as e:
        logger.error(f"Erreur lors de la validation Unity: {e}")
        return (False, [f"Erreur de validation: {str(e)}"])


def schema_exists() -> bool:
    """Vérifie si le schéma Unity est disponible.
    
    Returns:
        True si le fichier de schéma existe, False sinon.
    """
    return _SCHEMA_PATH.exists()




