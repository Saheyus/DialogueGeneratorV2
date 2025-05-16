import logging

logger = logging.getLogger(__name__)

class PromptEngine:
    def __init__(self, system_prompt_template=None):
        if system_prompt_template is None:
            self.system_prompt_template = self._get_default_system_prompt()
        else:
            self.system_prompt_template = system_prompt_template

    def _get_default_system_prompt(self):
        """
        Retourne un system prompt par défaut pour la génération de dialogues Yarn.
        """
        # Ce prompt est un point de départ et devra être considérablement enrichi.
        # Il manque : la structure exacte de Yarn attendue, des exemples,
        # des instructions sur la gestion des conditions (<<if>>), commandes (<<...>>),
        # le ton, le style RPG, etc.
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

    def build_prompt(self, context_summary: str, user_specific_goal: str, generation_params: dict = None) -> tuple[str, int]:
        """
        Construit le prompt final à envoyer au LLM.

        Args:
            context_summary (str): Un résumé textuel du contexte (personnages, lieu, scène).
            user_specific_goal (str): L'instruction spécifique de l'utilisateur pour la scène.
            generation_params (dict, optional): Paramètres additionnels (ton, style, nombre de répliques...). 
                                                Actuellement non utilisé en détail.

        Returns:
            tuple[str, int]: Le prompt complet et une estimation du nombre de mots.
        """
        if generation_params is None:
            generation_params = {}

        # Pour l'instant, une simple concaténation.
        # On pourra utiliser des f-strings ou des templates plus complexes plus tard.
        
        prompt_parts = [
            self.system_prompt_template,
            "\n--- CONTEXTE DE LA SCÈNE ---",
            context_summary,
            "\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---",
            user_specific_goal
        ]
        
        # Potentiellement ajouter d'autres sections basées sur generation_params
        # Par exemple:
        # if "tone" in generation_params:
        #     prompt_parts.append(f"\n--- TON ATTENDU ---")
        #     prompt_parts.append(generation_params["tone"])

        full_prompt = "\n".join(prompt_parts)
        word_count = len(full_prompt.split())
        logger.info(f"Prompt construit. Longueur approximative: {word_count} mots.")
        # logger.debug(f"Prompt complet:\n{full_prompt}") # Peut être très verbeux
        return full_prompt, word_count

# Pour des tests rapides
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
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
    dummy_params = {"tone": "Tendu, avec une pointe d'humour"}

    final_prompt, words = engine.build_prompt(dummy_context, dummy_user_goal, dummy_params)
    
    print("\n--- SYSTEM PROMPT UTILISÉ ---")
    print(engine.system_prompt_template)
    print("\n--- PROMPT FINAL GÉNÉRÉ POUR TEST ---")
    print(final_prompt)

    # Test avec un system prompt personnalisé
    custom_system_prompt = "Tu es un barde facétieux. Raconte une histoire drôle."
    custom_engine = PromptEngine(system_prompt_template=custom_system_prompt)
    custom_prompt, custom_words = custom_engine.build_prompt("Contexte: une taverne animée", "Le personnage principal glisse sur une peau de banane.")
    print("\n--- TEST AVEC SYSTEM PROMPT PERSONNALISÉ ---")
    print(custom_prompt)
    print(f"(Estim. mots: {custom_words})") 