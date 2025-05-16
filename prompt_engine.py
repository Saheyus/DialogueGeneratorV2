import logging
from typing import Tuple, Optional, Dict, Any

# Essayer d'importer tiktoken, mais continuer si non disponible
try:
    import tiktoken
    tiktoken_available = True
except ImportError:
    tiktoken_available = False
    tiktoken = None # Pour que les références ultérieures ne lèvent pas de NameError

logger = logging.getLogger(__name__)

class PromptEngine:
    """
    Gère la construction de prompts pour les modèles de langage.

    Cette classe combine un system prompt, un contexte de scène, et une instruction
    utilisateur pour créer un prompt final optimisé pour la génération de dialogue.
    """
    def __init__(self, system_prompt_template: Optional[str] = None) -> None:
        """
        Initialise le PromptEngine.

        Args:
            system_prompt_template (Optional[str]): Un template de system prompt personnalisé.
                                                    Si None, un prompt par défaut sera utilisé.
        """
        if system_prompt_template is None:
            self.system_prompt_template: str = self._get_default_system_prompt()
        else:
            self.system_prompt_template: str = system_prompt_template

    def _get_default_system_prompt(self) -> str:
        """
        Retourne un system prompt par défaut pour la génération de dialogues Yarn.

        Ce prompt sert de point de départ et peut être enrichi avec des détails
        sur la structure Yarn attendue, des exemples, des instructions sur la gestion
        des conditions (<<if>>), des commandes (<<command>>), le ton, le style RPG, etc.

        Returns:
            str: Le system prompt par défaut.
        """
        return \
"""
Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG).
Ta tâche est de générer un dialogue au format Yarn Spinner.
Le dialogue doit être cohérent avec le contexte fourni (personnages, lieu, quête).
Le dialogue doit suivre l'instruction utilisateur concernant l'objectif de la scène.

Format Yarn Spinner de base :
---
title: NomDuNoeud
tags: tag1 tag2
---
PersonnageA: Bonjour ! Ceci est une ligne de dialogue.
PersonnageB: Et ceci est une réponse.
    -> Option 1 [[NomDuNoeudSuivantOption1]]
        PersonnageA: Vous avez choisi l'option 1.
    -> Option 2
        PersonnageA: Vous avez choisi l'option 2.
<<jump NomDuNoeudDeFin>>
===
"""

    def _count_tokens(self, text: str, model_name: str = "gpt-4") -> int:
        """
        Compte le nombre de tokens dans un texte en utilisant tiktoken si disponible.

        Si tiktoken n'est pas disponible ou si une erreur se produit,
        un décompte approximatif basé sur les mots (séparés par des espaces) est utilisé.

        Args:
            text (str): Le texte pour lequel compter les tokens.
            model_name (str): Le nom du modèle à utiliser pour l'encodage (par défaut "gpt-4").
                              Cela influence la manière dont tiktoken compte les tokens.

        Returns:
            int: Le nombre estimé de tokens.
        """
        if tiktoken_available and tiktoken is not None:
            try:
                encoding = tiktoken.encoding_for_model(model_name)
                return len(encoding.encode(text))
            except Exception as e:
                logger.warning(f"Erreur lors du comptage des tokens avec tiktoken pour le modèle {model_name}: {e}. Repli sur le comptage de mots.")
                pass # Tomber vers le comptage de mots
        
        # Fallback si tiktoken n'est pas disponible ou a échoué
        return len(text.split())

    def build_prompt(
        self, 
        context_summary: str, 
        user_specific_goal: str, 
        generation_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Construit le prompt final à envoyer au LLM et estime son nombre de tokens.

        Args:
            context_summary (str): Un résumé textuel du contexte (personnages, lieu, scène).
            user_specific_goal (str): L'instruction spécifique de l'utilisateur pour la scène.
            generation_params (Optional[Dict[str, Any]]): Paramètres additionnels (ex: ton, style)
                                                           qui pourraient modifier le prompt.

        Returns:
            Tuple[str, int]: Le prompt complet et une estimation du nombre de tokens.
        """
        if generation_params is None:
            generation_params = {}

        prompt_parts = [
            self.system_prompt_template,
            "\n--- CONTEXTE DE LA SCÈNE ---",
            context_summary,
            "\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---",
            user_specific_goal
        ]
        
        # Exemple d'utilisation de generation_params (peut être étendu)
        if "tone" in generation_params:
            prompt_parts.append(f"\n--- TON ATTENDU ---")
            prompt_parts.append(str(generation_params["tone"]))

        full_prompt = "\n".join(prompt_parts)
        
        # Utiliser la nouvelle méthode _count_tokens
        num_tokens = self._count_tokens(full_prompt) 
        
        logger.info(f"Prompt construit. Longueur approximative: {num_tokens} tokens.")
        # logger.debug(f"Prompt complet:\n{full_prompt}") # Peut être très verbeux
        return full_prompt, num_tokens

# Pour des tests rapides
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])
    
    engine = PromptEngine()
    
    # Exemple de données factices
    dummy_context = \
"""
Personnages en scène:
- Elara: Une magicienne érudite mais impatiente. Cherche un artefact ancien.
- Gorok: Un guerrier bourru mais loyal. Protège Elara.
Lieu: Une vieille bibliothèque en ruines, remplie de parchemins et de dangers.
Quête actuelle: Trouver le Grimoire des Ombres.
"""
    dummy_user_goal = "Elara doit convaincre Gorok de la laisser explorer une section particulièrement dangereuse de la bibliothèque. Gorok est réticent."
    dummy_params: Dict[str, Any] = {"tone": "Tendu, avec une pointe d'humour"}

    final_prompt, tokens_count = engine.build_prompt(dummy_context, dummy_user_goal, dummy_params)
    
    print("\n--- SYSTEM PROMPT UTILISÉ ---")
    print(engine.system_prompt_template)
    print("\n--- PROMPT FINAL GÉNÉRÉ POUR TEST ---")
    print(final_prompt)
    print(f"\n(Estim. tokens: {tokens_count})")

    # Test avec un system prompt personnalisé
    custom_system_prompt = "Tu es un barde facétieux. Raconte une histoire drôle."
    custom_engine = PromptEngine(system_prompt_template=custom_system_prompt)
    custom_prompt, custom_tokens_count = custom_engine.build_prompt(
        "Contexte: une taverne animée", 
        "Le personnage principal glisse sur une peau de banane."
    )
    print("\n--- TEST AVEC SYSTEM PROMPT PERSONNALISÉ ---")
    print(custom_prompt)
    print(f"(Estim. tokens: {custom_tokens_count})") 