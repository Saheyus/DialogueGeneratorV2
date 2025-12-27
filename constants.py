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
    CONTEXT_BUILDER_NOT_AVAILABLE = "(ContextBuilder non disponible)"
    UNKNOWN_ITEM_ERROR = "(Erreur - Nom d'item inconnu)"
    UNITY_DIALOGUES_PATH_NOT_CONFIGURED = "Chemin des dialogues Unity non configuré."
    NO_JSON_FILES_FOUND = "(Aucun fichier JSON trouvé)"
    NO_ITEMS_CATEGORY_OR_FILTER = "(Aucun item pour cette catégorie ou filtre)"
    NO_MATCHING_JSON_FILES = "(Aucun fichier JSON correspondant)"
    NO_ITEMS = "(Aucun item)"

class FilePaths:
    CONFIG_DIR = Path("config")
    DATA_DIR = Path("data")
    INTERACTIONS_DIR = DATA_DIR / "interactions"
    LLM_USAGE_DIR = DATA_DIR / "llm_usage"
    LLM_CONFIG = "llm_config.json"

class Defaults:
    CONTEXT_TOKENS = 1500
    VARIANTS_COUNT = 2
    TEMPERATURE = 0.7
    MODEL_ID = "gpt-4o"
    MAX_TOKENS_FOR_CONTEXT_BUILDING = 32000
    SAVE_SETTINGS_DELAY_MS = 1000
    MAIN_SPLITTER_STRETCH_FACTOR_LEFT_PANEL = 1
    MAIN_SPLITTER_STRETCH_FACTOR_GENERATION_PANEL = 3
    MAX_TOKENS_MODEL = 4096
    INTERACTION_AUTOSAVE_INTERVAL_MS = 300000 # 5 minutes (nouvelle constante)

class ConfigFiles:
    UI_SETTINGS = "ui_settings.json" 