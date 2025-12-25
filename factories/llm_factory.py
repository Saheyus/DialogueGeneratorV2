import os
import logging
from llm_client import ILLMClient, OpenAIClient, DummyLLMClient

logger = logging.getLogger(__name__)

class LLMClientFactory:
    @staticmethod
    def create_client(model_id: str, config: dict, available_models: list[dict]) -> ILLMClient:
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
        logger.info(f"Tentative de création d'un client LLM pour model_id: {model_id}")

        if model_id == "dummy":
            logger.info("Création d'un DummyLLMClient (demandé explicitement).")
            return DummyLLMClient()

        model_config = next((m for m in available_models if m.get("model_identifier") == model_id), None)

        if not model_config:
            logger.warning(f"Configuration non trouvée pour model_id '{model_id}'. Utilisation de DummyLLMClient.")
            return DummyLLMClient()

        client_type = model_config.get("client_type")
        api_key_env_var = model_config.get("api_key_env_var")

        if client_type == "openai":
            if not api_key_env_var:
                logger.warning(f"Variable d'environnement pour la clé API non spécifiée pour le modèle OpenAI '{model_id}'. Utilisation de DummyLLMClient.")
                return DummyLLMClient()
            
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                logger.warning(f"Clé API non trouvée dans l'environnement (variable: {api_key_env_var}) pour le modèle OpenAI '{model_id}'. Utilisation de DummyLLMClient.")
                return DummyLLMClient()
            
            try:
                # La config passée à OpenAIClient est la config spécifique du modèle (model_config)
                # et non la config globale des LLM.
                logger.info(f"Création d'un OpenAIClient pour model_id: {model_id}")
                return OpenAIClient(api_key=api_key, model_config=model_config)
            except Exception as e:
                logger.error(f"Erreur lors de la création de OpenAIClient pour '{model_id}': {e}. Utilisation de DummyLLMClient.")
                return DummyLLMClient()
        
        # Ajouter d'autres types de clients ici si nécessaire (ex: Anthropic, Cohere)
        # elif client_type == "anthropic":
        #     # ... logique pour Anthropic ...
        #     pass

        logger.warning(f"Type de client LLM inconnu ou non supporté: '{client_type}' pour model_id '{model_id}'. Utilisation de DummyLLMClient.")
        return DummyLLMClient() 