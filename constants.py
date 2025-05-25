from pathlib import Path

class UIText:
    NONE = "(Aucun)"
    NONE_FEM = "(Aucune)"
    ALL = "(Tous / Non spécifié)"
    NO_SELECTION = "(Sélectionner une région d'abord)"
    NONE_SUBLOCATION = "(Aucun sous-lieu)"
    LOADING = "Chargement..."
    ERROR_PREFIX = "Erreur: "
    NO_INTERACTION_FOUND = "Aucune interaction trouvée."
    NO_PATH_FOUND = "Aucun chemin trouvé pour l'interaction {interaction_id}."
    NO_VARIANT = "Aucune variante n'a été générée par le LLM ou une erreur s'est produite."
    NO_MODEL_CONFIGURED = "Aucun modèle configuré"

class FilePaths:
    CONFIG_DIR = Path("config")
    DATA_DIR = Path("data")
    INTERACTIONS_DIR = DATA_DIR / "interactions"
    LLM_CONFIG = "llm_config.json"

class Defaults:
    CONTEXT_TOKENS = 1500
    VARIANTS_COUNT = 2
    TEMPERATURE = 0.7
    MODEL_ID = "gpt-4o"
    SAVE_SETTINGS_DELAY_MS = 1500
    MAX_TOKENS_FOR_CONTEXT_BUILDING = 32000 