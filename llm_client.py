# DialogueGenerator/llm_client.py
import asyncio
import logging
import os
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
import json # Ajout pour charger la config
from pathlib import Path # Ajout pour le chemin de la config

logger = logging.getLogger(__name__)

# Chemin vers le fichier de configuration LLM
LLM_CONFIG_PATH = Path(__file__).resolve().parent / "llm_config.json"

class ILLMClient(ABC):
    """Interface pour les clients LLM."""
    @abstractmethod
    async def generate_variants(self, prompt: str, k: int) -> list[str]:
        """
        Génère k variantes de texte à partir du prompt donné.

        Args:
            prompt (str): Le prompt à envoyer au LLM.
            k (int): Le nombre de variantes à générer.

        Returns:
            list[str]: Une liste de k chaînes de caractères, chaque chaîne étant une variante.
        """
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Retourne le nombre maximum de tokens que le modèle peut gérer pour un prompt."""
        pass

    async def close(self):
        # Implementation of close method
        pass

class DummyLLMClient(ILLMClient):
    def __init__(self, delay_seconds: float = 0.0):
        super().__init__()
        self.delay_seconds = delay_seconds
        logger.info(f"DummyLLMClient initialisé avec un délai de {self.delay_seconds}s par variante.")

    async def generate_variants(self, prompt: str, k: int) -> list[str]:
        logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Début de la génération de {k} variante(s)...")
        variants = []
        for i in range(k):
            if self.delay_seconds > 0:
                await asyncio.sleep(self.delay_seconds)
            variant_text = f"""---title: TitreDummy_Variant{i+1}_{k}
tags: tag_dummy
character_a: PersonnageA_Dummy
character_b: PersonnageB_Dummy
scene: Scene_Dummy
---
// Ceci est le corps de la variante {i+1} générée par DummyLLMClient.
// Prompt reçu : {prompt[:50]}...
<<ligne_de_dialogue_dummy_{i+1}>>
===
"""
            variants.append(variant_text)
            logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Variante {i+1} générée.")
        logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Génération de {k} variante(s) terminée.")
        return variants

    def get_max_tokens(self) -> int:
        return 16000 # Valeur arbitraire pour le client factice

    async def close(self):
        # Implementation of close method
        pass

class OpenAIClient(ILLMClient):
    def __init__(self, model_identifier: str, api_key_env_var: str = "OPENAI_API_KEY"):
        """
        Initialise le client OpenAI.

        Args:
            model_identifier (str): L'identifiant du modèle OpenAI à utiliser (ex: "gpt-4o").
            api_key_env_var (str): Le nom de la variable d'environnement contenant la clé API OpenAI.
        """
        self.api_key = os.getenv(api_key_env_var)
        if not self.api_key:
            logger.error(f"La variable d'environnement {api_key_env_var} n'est pas définie.")
            # Pour l'instant, on logue l'erreur et on continue, mais les appels échoueront.
            # Il serait préférable de lever une exception ici pour une gestion d'erreur plus robuste.
            # raise ValueError(f"{api_key_env_var} non configurée.")
        
        self.model = model_identifier
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        logger.info(f"OpenAIClient initialisé pour le modèle: {self.model}. Clé API chargée depuis {api_key_env_var}: {'Oui' if self.api_key else 'Non'}")

    @classmethod
    def load_llm_config(cls) -> dict:
        """Charge la configuration depuis llm_config.json."""
        try:
            with open(LLM_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Fichier de configuration LLM introuvable: {LLM_CONFIG_PATH}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Erreur de décodage JSON dans {LLM_CONFIG_PATH}")
            return {}
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement de {LLM_CONFIG_PATH}: {e}")
            return {}

    async def generate_variants(self, prompt: str, k: int) -> list[str]:
        if not self.client:
            error_msg = "OpenAIClient n'a pas pu être initialisé (clé API manquante ou autre erreur)."
            logger.error(error_msg)
            return [f"Erreur: {error_msg}"] * k

        variants = []
        logger.info(f"OpenAIClient: Envoi de la requête pour {k} variante(s) au modèle {self.model}.")
        try:
            # Pour obtenir k variantes distinctes, nous faisons k appels séparés.
            # L'API ChatCompletion ne garantit pas k choix distincts avec le paramètre `n` 
            # si `temperature` est bas. Faire k appels est plus explicite.
            tasks = []
            for _ in range(k):
                tasks.append(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG) au format Yarn Spinner."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7, # Un peu de créativité
                        # max_tokens=1000 # Ajuster au besoin, attention aux coûts
                    )
                )
            
            responses = await asyncio.gather(*tasks)
            
            for i, response in enumerate(responses):
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    variants.append(response.choices[0].message.content.strip())
                    logger.info(f"OpenAIClient: Variante {i+1}/{k} reçue.")
                else:
                    logger.warning(f"OpenAIClient: Réponse inattendue ou vide pour la variante {i+1}.")
                    variants.append("// Erreur: Réponse vide ou malformée du LLM.")
            
            logger.info(f"OpenAIClient: {len(variants)} variante(s) reçue(s) avec succès.")

        except Exception as e:
            logger.error(f"OpenAIClient: Erreur lors de l'appel à l'API OpenAI: {e}")
            # Renvoyer des messages d'erreur pour chaque variante attendue
            variants = [f"// Erreur lors de la génération OpenAI: {e}"] * k
        
        return variants

    def get_max_tokens(self) -> int:
        # Ces valeurs peuvent dépendre du modèle spécifique.
        # Pour gpt-4o-mini, la fenêtre de contexte est de 128K tokens.
        # Pour gpt-3.5-turbo, c'est souvent 4k ou 16k selon la version.
        # Retournons une valeur "générale" pour l'instant, ou adaptons selon self.model.
        if "gpt-4o-mini" in self.model:
            return 128000 # Fenêtre de contexte totale
        elif "gpt-4" in self.model: # inclut gpt-4, gpt-4-turbo, etc.
            return 128000
        elif "gpt-3.5-turbo-16k" in self.model:
            return 16384
        elif "gpt-3.5-turbo" in self.model:
            return 4096
        else:
            return 4096 # Par défaut pour les autres modèles gpt-3.5 ou inconnus

# Pour des tests rapides (nécessite que OPENAI_API_KEY soit définie dans l'environnement)
async def main_test():
    logging.basicConfig(level=logging.INFO)
    
    # Charger la configuration LLM pour le test
    llm_config = OpenAIClient.load_llm_config()
    default_model = llm_config.get("default_model_identifier", "gpt-3.5-turbo")
    api_key_var = llm_config.get("api_key_env_var", "OPENAI_API_KEY")

    # Test Dummy
    dummy_client = DummyLLMClient()
    dummy_prompt = "Instructions pour le dummy..."
    dummy_variants = await dummy_client.generate_variants(dummy_prompt, 2)
    print("\n--- Variants du DummyLLMClient ---")
    for i, v in enumerate(dummy_variants):
        print(f"Variante {i+1}:\n{v}\n")

    # Test OpenAI
    openai_client = OpenAIClient(model_identifier=default_model, api_key_env_var=api_key_var)
    if not openai_client.api_key:
        print(f"{api_key_var} n'est pas configurée. Le test OpenAI sera sauté.")
        return

    # Récupérer le system prompt et le contexte du PromptEngine pour un test plus réaliste
    from prompt_engine import PromptEngine
    engine = PromptEngine()
    test_context = "PersonnageA: Bob, PersonnageB: Alice, Lieu: Taverne"
    test_user_goal = "Bob veut commander une bière à Alice."
    openai_prompt, _ = engine.build_prompt(test_context, test_user_goal)
    
    print(f"\n--- Envoi du prompt suivant à {openai_client.model} ---")
    print(openai_prompt)
    print("--------------------------------------------------")

    openai_variants = await openai_client.generate_variants(openai_prompt, 1) # Test avec 1 variante pour commencer
    print(f"\n--- Variants de l'OpenAIClient ({openai_client.model}) ---")
    for i, v in enumerate(openai_variants):
        print(f"Variante {i+1}:\n{v}\n")

if __name__ == '__main__':
    # Pour exécuter le test async : python -m DialogueGenerator.llm_client 
    # (si vous êtes dans le dossier parent Notion_Scrapper)
    # ou simplement `python llm_client.py` si vous êtes dans `DialogueGenerator`
    asyncio.run(main_test()) 