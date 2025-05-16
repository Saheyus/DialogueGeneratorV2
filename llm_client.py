# DialogueGenerator/llm_client.py
import asyncio
import logging
import os
from abc import ABC, abstractmethod
from openai import AsyncOpenAI # Importer AsyncOpenAI

logger = logging.getLogger(__name__)

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

class DummyLLMClient(ILLMClient):
    def __init__(self, delay_seconds=0.5):
        self.delay_seconds = delay_seconds
        logger.info(f"DummyLLMClient initialisé avec un délai de {self.delay_seconds}s par variante.")

    async def generate_variants(self, prompt: str, k: int) -> list[str]:
        logger.info(f"DummyLLMClient: Début de la génération de {k} variante(s)...")
        variants = []
        for i in range(k):
            await asyncio.sleep(self.delay_seconds) # Simule un appel réseau
            # Simuler une réponse de LLM au format Yarn
            variant_text = f"""---title: NomDuNoeud_Variant{i+1}
tags: dummy_tag generated
---
Narrateur: Ceci est la variante numéro {i+1} générée par DummyLLMClient.
Narrateur: L'objectif utilisateur était : '{prompt.split("--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---")[-1].strip()}'
Narrateur: Le prompt de base contenait environ {len(prompt.split())} mots.
PersonnageFacticeA: Le prompt de base contenait environ {len(prompt.split())} mots.
PersonnageFacticeB: C'est une réponse simulée pour tester le flux.
    -> Option simulée 1
        Narrateur: Action pour l'option 1.
    -> Option simulée 2
        Narrateur: Action pour l'option 2.
<<jump FinSceneSimulee_Variant{i+1}>>
==="""
            variants.append(variant_text)
            logger.info(f"DummyLLMClient: Variante {i+1} générée.")
        logger.info(f"DummyLLMClient: Génération de {k} variante(s) terminée.")
        return variants

class OpenAIClient(ILLMClient):
    def __init__(self, model="gpt-3.5-turbo"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("La variable d'environnement OPENAI_API_KEY n'est pas définie.")
            # Vous pourriez lever une exception ici ou gérer cela d'une autre manière
            # Pour l'instant, on logue l'erreur et on continue, mais les appels échoueront.
            # raise ValueError("OPENAI_API_KEY non configurée.")
        self.model = model
        # Initialiser le client AsyncOpenAI seulement si la clé API est présente
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        logger.info(f"OpenAIClient initialisé pour le modèle: {self.model}. Clé API chargée: {'Oui' if self.api_key else 'Non'}")

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

# Pour des tests rapides (nécessite que OPENAI_API_KEY soit définie dans l'environnement)
async def main_test():
    logging.basicConfig(level=logging.INFO)
    
    # Test Dummy
    dummy_client = DummyLLMClient()
    dummy_prompt = "Instructions pour le dummy..."
    dummy_variants = await dummy_client.generate_variants(dummy_prompt, 2)
    print("\n--- Variants du DummyLLMClient ---")
    for i, v in enumerate(dummy_variants):
        print(f"Variante {i+1}:\n{v}\n")

    # Test OpenAI
    openai_client = OpenAIClient(model="gpt-3.5-turbo") # ou "gpt-4o-mini"
    if not openai_client.api_key:
        print("OPENAI_API_KEY n'est pas configurée. Le test OpenAI sera sauté.")
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