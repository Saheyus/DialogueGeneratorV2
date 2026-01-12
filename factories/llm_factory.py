import os
import json
import time
import logging
from typing import Optional, Any
from core.llm.llm_client import ILLMClient, OpenAIClient, DummyLLMClient

logger = logging.getLogger(__name__)

class LLMClientFactory:
    @staticmethod
    def create_client(
        model_id: str,
        config: dict,
        available_models: list[dict],
        usage_service: Optional[Any] = None,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> ILLMClient:
        """
        Crée un client LLM basé sur model_id et la configuration.

        Args:
            model_id: L'identifiant du modèle à utiliser (ex: "gpt-4o", "dummy").
            config: La configuration globale des LLM (issue de llm_config.json).
                    Utilisé pour trouver les détails spécifiques du modèle comme 
                    la variable d'env pour la clé API.
            available_models: La liste des modèles disponibles avec leurs configurations.

        Returns:
            Une instance de ILLMClient (OpenAIClient ou DummyLLMClient).
            Retourne DummyLLMClient si le modèle n'est pas trouvé,
            si la clé API est manquante pour OpenAI, ou en cas d'erreur.
        """
        if model_id == "dummy":
            return DummyLLMClient()

        # Mapper les anciens identifiants vers les nouveaux (compatibilité)
        model_id_mapping = {
            "gpt-5.2-thinking": "gpt-5.2-pro"  # Ancien identifiant inexistant → nouveau identifiant valide
        }
        if model_id in model_id_mapping:
            logger.warning(f"Modèle '{model_id}' est déprécié. Utilisation de '{model_id_mapping[model_id]}' à la place.")
            model_id = model_id_mapping[model_id]

        # Chercher le modèle par api_identifier (champ dans llm_config.json) ou model_identifier (compatibilité)
        model_config = next(
            (m for m in available_models 
             if m.get("api_identifier") == model_id or m.get("model_identifier") == model_id), 
            None
        )

        if not model_config:
            logger.warning(f"Configuration non trouvée pour model_id '{model_id}'. Utilisation de DummyLLMClient.")
            return DummyLLMClient()

        client_type = model_config.get("client_type", "openai")  # Par défaut openai
        # La clé API est dans la config globale, pas dans chaque modèle
        api_key_env_var = config.get("api_key_env_var")

        if client_type == "openai":
            if not api_key_env_var:
                logger.warning(f"Variable d'environnement pour la clé API non spécifiée pour le modèle OpenAI '{model_id}'. Utilisation de DummyLLMClient.")
                return DummyLLMClient()
            
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                logger.warning(f"Clé API non trouvée dans l'environnement (variable: {api_key_env_var}) pour le modèle OpenAI '{model_id}'. Utilisation de DummyLLMClient.")
                return DummyLLMClient()
            
            try:
                # La config passée à OpenAIClient doit contenir default_model avec l'identifiant du modèle
                # On construit une config compatible avec OpenAIClient qui attend "default_model"
                model_identifier = model_config.get("api_identifier") or model_config.get("model_identifier") or model_id
                client_config = config.copy()  # Commencer avec la config globale
                client_config["default_model"] = model_identifier  # Définir le modèle spécifique
                # Ajouter les paramètres du modèle s'ils existent
                if "parameters" in model_config:
                    if "default_temperature" in model_config["parameters"]:
                        client_config["temperature"] = model_config["parameters"]["default_temperature"]
                    if "max_tokens" in model_config["parameters"]:
                        client_config["max_tokens"] = model_config["parameters"]["max_tokens"]
                logger.info(f"Création d'un OpenAIClient pour model_id: {model_id} (default_model: {model_identifier})")
                # #region agent log
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "D",
                    "location": "llm_factory.py:create_client",
                    "message": "Création OpenAIClient - modèle sélectionné",
                    "data": {
                        "model_id": model_id,
                        "model_identifier": model_identifier,
                        "api_identifier": model_config.get("api_identifier"),
                        "model_identifier_from_config": model_config.get("model_identifier"),
                        "display_name": model_config.get("display_name")
                    },
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    with open(r"f:\Projets\Notion_Scrapper\DialogueGenerator\.cursor\debug.log", "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(log_data) + "\n")
                except: pass
                # #endregion
                return OpenAIClient(
                    api_key=api_key,
                    config=client_config,
                    usage_service=usage_service,
                    request_id=request_id,
                    endpoint=endpoint
                )
            except Exception as e:
                logger.error(f"Erreur lors de la création de OpenAIClient pour '{model_id}': {e}. Utilisation de DummyLLMClient.")
                return DummyLLMClient()
        
        # Ajouter d'autres types de clients ici si nécessaire (ex: Anthropic, Cohere)
        # elif client_type == "anthropic":
        #     # ... logique pour Anthropic ...
        #     pass

        logger.warning(f"Type de client LLM inconnu ou non supporté: '{client_type}' pour model_id '{model_id}'. Utilisation de DummyLLMClient.")
        return DummyLLMClient() 