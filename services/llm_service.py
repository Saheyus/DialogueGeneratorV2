"""LLM Service for managing Language Model clients and operations."""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# Assuming ILLMClient, OpenAIClient, DummyLLMClient are in a reachable path
# This might need adjustment based on your project structure for imports
try:
    from ..llm_client import ILLMClient, OpenAIClient, DummyLLMClient
except ImportError:
    # Fallback for direct execution or different structure
    # You might need to add DialogueGenerator to sys.path if running this file directly
    # For now, let's assume they will be found if DialogueGenerator is in PYTHONPATH
    from DialogueGenerator.llm_client import ILLMClient, OpenAIClient, DummyLLMClient

logger = logging.getLogger(__name__)

DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json"

class LLMService:
    def __init__(self):
        self.llm_config: Dict[str, Any] = self._load_json_file(LLM_CONFIG_FILE_PATH, default=self._get_default_llm_config_data())
        self.available_models: List[Dict[str, Any]] = self.llm_config.get("available_models", [])
        self.current_client: Optional[ILLMClient] = None
        self._ensure_config_defaults()

    def _get_default_llm_config_data(self) -> Dict[str, Any]:
        """Returns a default LLM configuration dictionary."""
        return {
            "api_key_env_var": "OPENAI_API_KEY",
            "default_model_identifier": "dummy",
            "request_timeout": 60,
            "temperature": 0.7,
            "max_tokens": 2048,
            "available_models": [
                {
                    "display_name": "Dummy Client (Default)", 
                    "api_identifier": "dummy", 
                    "notes": "Fallback/Default client. Produces placeholder text. Supports simulated structured output.",
                    "supports_json_mode": True
                }
            ]
        }

    def _ensure_config_defaults(self):
        """Ensures that the loaded config has essential default model if empty and dummy is configured for structured output."""
        default_dummy_config = self._get_default_llm_config_data()["available_models"][0]

        if not self.available_models:
            logger.warning("No models found in llm_config.json, adding default Dummy client configured for structured output.")
            self.available_models.append(default_dummy_config.copy())
            self.llm_config["available_models"] = self.available_models
            # self.save_llm_config(self.llm_config) # Optionnel: sauvegarder immédiatement
        else:
            # Vérifier si le dummy existe et s'il a supports_json_mode: True
            dummy_model_found = False
            for model_config in self.available_models:
                if model_config.get("api_identifier") == "dummy":
                    dummy_model_found = True
                    if not model_config.get("supports_json_mode"):
                        logger.info("Forcing 'supports_json_mode: True' for existing 'dummy' model in llm_config.json.")
                        model_config["supports_json_mode"] = True
                        # Optionnel: sauvegarder si modifié
                        # self.save_llm_config(self.llm_config)
                    break
            if not dummy_model_found:
                logger.warning("No 'dummy' model found in llm_config.json available_models. Adding default dummy model.")
                self.available_models.append(default_dummy_config.copy())
                self.llm_config["available_models"] = self.available_models
                # self.save_llm_config(self.llm_config)

        default_id = self.llm_config.get("default_model_identifier", "dummy")
        if not any(model['api_identifier'] == default_id for model in self.available_models):
            logger.warning(f"Default model '{default_id}' not in available models. Setting to first available or dummy.")
            if self.available_models:
                self.llm_config["default_model_identifier"] = self.available_models[0]["api_identifier"]
            else:
                self.llm_config["default_model_identifier"] = "dummy" # Devrait être couvert par le bloc plus haut

    def _load_json_file(self, file_path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if default is None:
            default = {}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Error decoding {file_path}. Returning default.")
                return default.copy() # Return a copy to avoid modifying the default dict
            except IOError as e:
                logger.error(f"Could not read {file_path}: {e}. Returning default.")
                return default.copy()
        else:
            logger.info(f"{file_path} not found. Returning default configuration.")
            # If the file doesn't exist, we should save the default config to it.
            if default: # Ensure default is not None
                 self._save_json_file(file_path, default) # Save the default config
            return default.copy()

    def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except IOError:
            logger.error(f"Could not write to {file_path}.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving to {file_path}: {e}")
            return False

    def get_llm_config(self) -> Dict[str, Any]:
        return self.llm_config.copy()

    def get_llm_setting(self, key: str, default: Any = None) -> Any:
        return self.llm_config.get(key, default)

    def save_llm_config(self, config: Dict[str, Any]) -> bool:
        self.llm_config = config.copy()
        # Re-evaluate available models from the new config
        self.available_models = self.llm_config.get("available_models", [])
        self._ensure_config_defaults() # Ensure defaults are still valid
        return self._save_json_file(LLM_CONFIG_FILE_PATH, self.llm_config)

    def get_available_models(self) -> List[Dict[str, Any]]:
        return self.available_models[:]
    
    def get_default_model_identifier(self) -> str:
        return self.llm_config.get("default_model_identifier", "dummy")

    def create_client(self, model_identifier: Optional[str] = None) -> ILLMClient:
        effective_model_id = model_identifier if model_identifier else self.get_default_model_identifier()
        
        logger.info(f"Creating LLM client for model: {effective_model_id}")
        api_key_var = self.llm_config.get("api_key_env_var", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_var)

        client_config = self.llm_config.copy()
        client_config["model_name"] = effective_model_id

        model_properties = next((m for m in self.available_models if m["api_identifier"] == effective_model_id), None)
        if model_properties:
            client_config.update(model_properties)

        try:
            if effective_model_id.lower() == "dummy":
                self.current_client = DummyLLMClient()
            elif "openai" in effective_model_id.lower() or any(m.get("provider") == "openai" for m in self.available_models if m["api_identifier"] == effective_model_id):
                self.current_client = OpenAIClient(api_key=api_key, config=client_config)
            else:
                logger.warning(f"Unknown model provider for '{effective_model_id}'. Falling back to DummyLLMClient.")
                self.current_client = DummyLLMClient()
            
            logger.info(f"LLM Client created: {type(self.current_client).__name__} for model '{effective_model_id}'.")
            return self.current_client
        except Exception as e:
            logger.error(f"Error creating LLM client for '{effective_model_id}': {e}", exc_info=True)
            logger.warning("Falling back to DummyLLMClient due to error.")
            self.current_client = DummyLLMClient()
            return self.current_client

    def get_current_client(self) -> Optional[ILLMClient]:
        """Returns the currently active LLM client, creating one if it doesn't exist."""
        if not self.current_client:
            logger.info("No current LLM client. Creating default client.")
            self.create_client() # Creates default and sets self.current_client
        return self.current_client

    def switch_model(self, new_model_identifier: str) -> Optional[ILLMClient]:
        logger.info(f"Switching LLM model to: {new_model_identifier}")
        if not any(model['api_identifier'] == new_model_identifier for model in self.available_models):
            logger.error(f"Model identifier '{new_model_identifier}' not found in available models. Cannot switch.")
            # Optionally, could fall back to default or return None without changing client
            # For now, let's not change the client if the new model is invalid.
            return self.current_client 
            
        self.create_client(new_model_identifier) # This will update self.current_client
        # Save this new model as the default for next time?
        # Current behavior of MainWindow saves the 'current_llm_model_identifier' in ui_settings.
        # LLMService itself could also store its 'active_model_identifier' in llm_config if desired.
        # self.llm_config["default_model_identifier"] = new_model_identifier # Example
        # self.save_llm_config(self.llm_config) # Example
        return self.current_client 