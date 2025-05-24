"""Configuration Service for managing application settings."""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union # Added Union
import logging

logger = logging.getLogger(__name__)

# Define paths at the module level or pass them during instantiation
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
UI_SETTINGS_FILE = DIALOGUE_GENERATOR_DIR / "ui_settings.json"
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json"
CONTEXT_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "context_config.json"

# Chemin par défaut pour les dialogues Unity - pourrait être une constante de classe ou globale
DEFAULT_UNITY_DIALOGUES_PATH = Path("F:/Unity/Alteir/Alteir_Cursor/Assets/Dialogue/generated")

class ConfigurationService:
    def __init__(self):
        self.ui_settings: Dict[str, Any] = self._load_json_file(UI_SETTINGS_FILE, default={})
        self.llm_config: Dict[str, Any] = self._load_json_file(LLM_CONFIG_FILE_PATH, default={})
        self.context_config: Dict[str, Any] = self._load_json_file(CONTEXT_CONFIG_FILE_PATH, default={})

        # Initialiser les chemins importants lors de l'instanciation
        # Ou les récupérer dynamiquement via des getters
        self.unity_dialogues_path: Optional[Path] = self._initialize_unity_dialogues_path()

    def _load_json_file(self, file_path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Loads a JSON file.

        Args:
            file_path (Path): The path to the JSON file.
            default (Optional[Dict[str, Any]]): Default dictionary to return if file not found or invalid.

        Returns:
            Dict[str, Any]: The loaded data or default.
        """
        if default is None:
            default = {}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Error decoding {file_path}. Returning default: {default}")
                return default
            except IOError as e:
                logger.error(f"Could not read {file_path}: {e}. Returning default: {default}")
                return default
        return default

    def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Saves data to a JSON file.

        Args:
            file_path (Path): The path to the JSON file.
            data (Dict[str, Any]): The data to save.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except IOError:
            logger.error(f"Could not write to {file_path}.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving to {file_path}: {e}")
            return False

    # --- UI Settings specific methods ---
    def get_ui_setting(self, key: str, default: Any = None) -> Any:
        """Gets a specific UI setting."""
        return self.ui_settings.get(key, default)

    def get_all_ui_settings(self) -> Dict[str, Any]:
        """Gets all UI settings."""
        return self.ui_settings.copy()

    def update_ui_setting(self, key: str, value: Any) -> None:
        """Updates a single UI setting."""
        self.ui_settings[key] = value
    
    def update_all_ui_settings(self, settings: Dict[str, Any]) -> None:
        """Replaces all UI settings with the provided dictionary."""
        self.ui_settings = settings.copy() # Ensure we're working with a copy

    def save_ui_settings(self) -> bool:
        """Saves current UI settings to the file."""
        return self._save_json_file(UI_SETTINGS_FILE, self.ui_settings)

    # --- Context Config specific methods ---
    def get_context_config(self) -> Dict[str, Any]:
        """Gets the context configuration."""
        return self.context_config.copy()

    def save_context_config(self, config: Dict[str, Any]) -> bool:
        """Saves context configuration to the file."""
        self.context_config = config.copy()
        return self._save_json_file(CONTEXT_CONFIG_FILE_PATH, self.context_config)

    # --- File Path Getters ---
    def get_ui_settings_file_path(self) -> Path:
        return UI_SETTINGS_FILE

    def get_llm_config_file_path(self) -> Path:
        return LLM_CONFIG_FILE_PATH

    def get_context_config_file_path(self) -> Path:
        return CONTEXT_CONFIG_FILE_PATH

    # --- Unity Dialogues Path specific methods (from config_manager.py) ---
    def _initialize_unity_dialogues_path(self) -> Optional[Path]:
        """Initializes and validates the Unity dialogues path."""
        path_str = self.get_ui_setting("unity_dialogues_path")
        
        dialogues_path = None
        if path_str:
            dialogues_path = Path(path_str)
        else:
            dialogues_path = DEFAULT_UNITY_DIALOGUES_PATH
            logger.info(f"Unity dialogues path not configured, using default: {dialogues_path}")
            # Save the default path to ui_settings if it wasn't there
            self.update_ui_setting("unity_dialogues_path", str(dialogues_path))
            self.save_ui_settings() # Persist this change

        if not self._validate_and_prepare_path(dialogues_path):
            # If validation fails for the (default or loaded) path, try the default path explicitly one more time
            # This handles cases where the stored path is bad, but the default is good.
            if dialogues_path != DEFAULT_UNITY_DIALOGUES_PATH:
                logger.warning(f"Initial Unity dialogues path '{dialogues_path}' is invalid. Trying default path '{DEFAULT_UNITY_DIALOGUES_PATH}'.")
                self.update_ui_setting("unity_dialogues_path", str(DEFAULT_UNITY_DIALOGUES_PATH))
                self.save_ui_settings()
                if self._validate_and_prepare_path(DEFAULT_UNITY_DIALOGUES_PATH):
                    return DEFAULT_UNITY_DIALOGUES_PATH
            logger.error(f"Unity dialogues path '{dialogues_path}' (and default, if tried) is invalid and could not be prepared.")
            return None
        return dialogues_path

    def _validate_and_prepare_path(self, path_to_validate: Path) -> bool:
        """Validates a path: ensures it exists (creates if not), is a directory, and is R/W."""
        if not path_to_validate.exists():
            try:
                path_to_validate.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path_to_validate}")
            except Exception as e:
                logger.error(f"Could not create directory: {path_to_validate}. Error: {e}")
                return False
        
        if not path_to_validate.is_dir():
            logger.error(f"Path is not a directory: {path_to_validate}")
            return False
        
        if not os.access(path_to_validate, os.W_OK):
            logger.error(f"Path is not writable: {path_to_validate}")
            return False
        
        if not os.access(path_to_validate, os.R_OK):
            logger.error(f"Path is not readable: {path_to_validate}")
            return False
        return True

    def get_unity_dialogues_path(self) -> Optional[Path]:
        """Returns the currently configured and validated Unity dialogues path."""
        # Re-validate every time it's requested to ensure it's still valid?
        # Or trust the one initialized, and rely on set_unity_dialogues_path for changes.
        # For now, returning the initialized one. If it was None, means it failed init.
        if self.unity_dialogues_path and self._validate_and_prepare_path(self.unity_dialogues_path):
            return self.unity_dialogues_path
        
        # If current path is None or became invalid, try to re-initialize
        logger.warning("Current Unity dialogues path is invalid or not set. Attempting to re-initialize.")
        self.unity_dialogues_path = self._initialize_unity_dialogues_path()
        return self.unity_dialogues_path

    def set_unity_dialogues_path(self, new_path_str: Union[str, Path]) -> bool:
        """Sets and saves the new Unity dialogues path after validation."""
        new_path = Path(new_path_str)
        
        if not self._validate_and_prepare_path(new_path):
            logger.warning(f"Proposed Unity dialogues path '{new_path}' is invalid or could not be prepared.")
            return False

        self.update_ui_setting("unity_dialogues_path", str(new_path))
        if self.save_ui_settings():
            self.unity_dialogues_path = new_path
            logger.info(f"Unity dialogues path configured: {new_path}")
            return True
        else:
            logger.error(f"Failed to save UI settings after updating Unity dialogues path to '{new_path}'.")
            return False

# Example usage (optional, for testing or demonstration)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config_service = ConfigurationService()
    
    print(f"UI Settings File: {UI_SETTINGS_FILE}")
    print(f"LLM Config File: {LLM_CONFIG_FILE_PATH}")
    print(f"Context Config File: {CONTEXT_CONFIG_FILE_PATH}")

    print("\n--- Initial Configs ---")
    print(f"Initial UI settings: {config_service.get_all_ui_settings()}")
    print(f"Initial LLM config: {config_service.get_llm_config()}")
    print(f"Initial Context config: {config_service.get_context_config()}")
    print(f"Initial Unity Dialogues Path: {config_service.get_unity_dialogues_path()}")

    print("\n--- Modifying UI Setting ---")
    config_service.update_ui_setting("test_setting", "test_value")
    config_service.update_ui_setting("window_width", 1024)
    print(f"UI settings after update: {config_service.get_ui_setting('test_setting')}, {config_service.get_ui_setting('window_width')}")
    if config_service.save_ui_settings():
        print("UI settings saved successfully.")
    else:
        print("Failed to save UI settings.")

    print("\n--- Testing Unity Dialogues Path ---")
    # Test setting a new path (ensure the test_path directory can be created or exists)
    test_dialogue_path = DIALOGUE_GENERATOR_DIR / "test_dialogues_output"
    print(f"Attempting to set Unity dialogues path to: {test_dialogue_path}")
    if config_service.set_unity_dialogues_path(str(test_dialogue_path)):
        print(f"Successfully set Unity dialogues path to: {config_service.get_unity_dialogues_path()}")
    else:
        print(f"Failed to set Unity dialogues path to: {test_dialogue_path}")
    
    # Test with an invalid path to see if it falls back or reports error
    invalid_path = "/invalid_path_that_should_not_exist_or_be_creatable"
    print(f"Attempting to set Unity dialogues path to an invalid path: {invalid_path}")
    if not config_service.set_unity_dialogues_path(invalid_path):
        print(f"Correctly failed to set invalid path. Current path: {config_service.get_unity_dialogues_path()}")
    else:
        print(f"Incorrectly set invalid path: {config_service.get_unity_dialogues_path()}")

    current_path = config_service.get_unity_dialogues_path()
    if current_path:
        print(f"Final validated Unity Dialogues Path: {current_path}")
    else:
        print("Final Unity Dialogues Path is not available or invalid.")

    print("\n--- Testing LLM Config --- (Assuming llm_config.json might be empty or have defaults)")
    available_models = config_service.get_available_llm_models()
    if available_models:
        print(f"Available LLM Models: {available_models}")
    else:
        print("No LLM models found in configuration or llm_config.json is empty/missing.")
        # Example: Saving a default LLM config if it's part of the service's role
        # default_llm_cfg = {"api_key_env_var": "OPENAI_API_KEY", "default_model_identifier": "gpt-4o-mini", "available_models": [{"display_name": "GPT-4o Mini", "api_identifier": "gpt-4o-mini"}]}
        # if config_service.save_llm_config(default_llm_cfg):
        #     print(f"Saved a default LLM config. Available models: {config_service.get_available_llm_models()}")
        # else:
        #     print("Failed to save default LLM config.") 