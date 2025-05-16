# DialogueGenerator/llm_client.py
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)

class IGenerator(ABC):
    """Interface pour les générateurs de texte via LLM."""

    @abstractmethod
    async def generate_variants(self, prompt: str, k: int) -> List[str]:
        """
        Génère k variantes de texte à partir d'un prompt donné.

        Args:
            prompt (str): Le prompt à envoyer au LLM.
            k (int): Le nombre de variantes à générer.

        Returns:
            List[str]: Une liste de k chaînes de caractères, chaque chaîne étant une variante.
        """
        pass

class DummyLLMClient(IGenerator):
    """
    Un client LLM factice pour les tests. 
    Ne fait pas d'appels réseau réels mais simule la génération.
    """
    def __init__(self, delay_seconds=0.5):
        self.delay_seconds = delay_seconds
        logger.info(f"DummyLLMClient initialisé avec un délai de {delay_seconds}s par variante.")

    async def generate_variants(self, prompt: str, k: int) -> List[str]:
        variants = []
        logger.info(f"DummyLLMClient: Début de la génération de {k} variante(s)...")
        
        # Pour rendre la simulation un peu plus réaliste, on extrait le "titre" potentiel
        # et l'objectif utilisateur du prompt s'ils sont formatés comme dans PromptEngine
        title_suggestion = "GeneratedNodeTitle"
        try:
            lines = prompt.split('\n')
            for i, line in enumerate(lines):
                if "title:" in line and i < len(lines) -1:
                    # Tentative de prendre ce qui suit "title: "
                    potential_title = line.split("title:",1)[1].strip()
                    if potential_title: 
                        title_suggestion = potential_title
                        break 
        except Exception:
            pass # Pas grave si on ne trouve pas
            
        user_goal_segment = ""
        try:
            if "--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---" in prompt:
                user_goal_segment = prompt.split("--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---", 1)[1].strip()
                if len(user_goal_segment) > 70:
                    user_goal_segment = user_goal_segment[:67] + "..."
        except Exception:
            pass

        for i in range(k):
            await asyncio.sleep(self.delay_seconds) # Simule le temps de traitement
            variant_content = f"""---title: {title_suggestion}_Variant{i+1}
tags: dummy_tag generated
---
Narrateur: Ceci est la variante numéro {i+1} générée par DummyLLMClient.
Narrateur: L'objectif utilisateur était : '{user_goal_segment}'

PersonnageFacticeA: Le prompt de base contenait environ {len(prompt.split())} mots.
PersonnageFacticeB: C'est une réponse simulée pour tester le flux.
    -> Option simulée 1
        Narrateur: Action pour l'option 1.
    -> Option simulée 2
        Narrateur: Action pour l'option 2.
<<jump FinSceneSimulee_Variant{i+1}>>
===
"""
            variants.append(variant_content)
            logger.info(f"DummyLLMClient: Variante {i+1} générée.")
        
        logger.info(f"DummyLLMClient: Génération de {k} variante(s) terminée.")
        return variants

# Pour des tests rapides
async def main_test():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    dummy_client = DummyLLMClient(delay_seconds=0.2)
    
    test_prompt = """Tu es un assistant. Contexte: PersonnageA, PersonnageB. Lieu: Forêt. Objectif: PersonnageA demande son chemin à PersonnageB.
--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---
Faire en sorte que PersonnageB réponde de manière énigmatique."""
    num_variants = 3
    
    print(f"\nDemande de {num_variants} variantes au DummyLLMClient...")
    generated_variants = await dummy_client.generate_variants(test_prompt, num_variants)
    
    print(f"\n--- {len(generated_variants)} VARIANTES GÉNÉRÉES ---")
    for idx, var_text in enumerate(generated_variants):
        print(f"\n--- Variante {idx+1} ---")
        print(var_text)

if __name__ == '__main__':
    asyncio.run(main_test()) 