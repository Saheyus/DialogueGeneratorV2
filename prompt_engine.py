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

    def _get_interaction_system_prompt(self) -> str:
        """
        Retourne un system prompt spécifique à la génération d'Interactions structurées.
        
        Ce prompt instruit le LLM à générer une structure JSON compatible avec le modèle
        Interaction et ses éléments associés (DialogueLineElement, PlayerChoicesBlockElement, etc.)
        
        Returns:
            str: Le system prompt pour la génération d'Interactions.
        """
        return \
"""
Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG).
Ta tâche est de générer une interaction structurée au format JSON.
L'interaction doit être cohérente avec le contexte fourni (personnages, lieu, quête).
L'interaction doit suivre l'instruction utilisateur concernant l'objectif de la scène.

SI UN HISTORIQUE DE DIALOGUE PRÉCÉDENT EST FOURNI DANS LE CONTEXTE, ASSURE-TOI QUE LA NOUVELLE INTERACTION EN SOIT LA SUITE LOGIQUE.

FORMAT JSON À RESPECTER STRICTEMENT:

```json
{
  "interaction_id": "un_id_unique_pour_cette_interaction",
  "title": "Titre descriptif de l'interaction",
  "elements": [
    {
      "element_type": "dialogue_line",
      "speaker": "Nom du personnage qui parle",
      "text": "Texte du dialogue"
    },
    {
      "element_type": "command",
      "command_string": "wait(2)"
    },
    {
      "element_type": "player_choices_block",
      "choices": [
        {
          "text": "Ce que le joueur peut dire/faire (option 1)",
          "next_interaction_id": "id_interaction_suivante_option_1"
        },
        {
          "text": "Ce que le joueur peut dire/faire (option 2)",
          "next_interaction_id": "id_interaction_suivante_option_2"
        }
      ]
    }
  ],
  "header_tags": ["tag1", "tag2"],
  "next_interaction_id_if_no_choices": null
}
```

RÈGLES À SUIVRE:
1. L'interaction doit être complète et autonome
2. L'ordre des éléments est important et sera respecté lors du rendu
3. Ne fournis que la structure JSON, sans explication ni commentaire
4. Utilise un ID d'interaction unique et descriptif (par exemple: "rencontre_tavernier_initial")
5. Pour les choix du joueur, invente des ID logiques pour les interactions suivantes (par exemple: "rencontre_tavernier_accepte_quete")
6. Les éléments peuvent être répétés (plusieurs lignes de dialogue, plusieurs commandes, etc.)
7. Utilise les personnages mentionnés dans le contexte comme "speaker" des lignes de dialogue
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
        user_specific_goal: str,
        scene_protagonists: Optional[Dict[str, str]] = None, # Format: {"personnage_a": "Nom A", "personnage_b": "Nom B"}
        scene_location: Optional[Dict[str, str]] = None, # Format: {"lieu": "Nom Lieu", "sous_lieu": "Nom Sous-Lieu"}
        context_summary: Optional[str] = None, # Le reste du contexte général
        generation_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Construit le prompt final à envoyer au LLM et estime son nombre de tokens.

        Args:
            user_specific_goal (str): L'instruction spécifique de l'utilisateur pour la scène.
            scene_protagonists (Optional[Dict[str, str]]): Dictionnaire identifiant le personnage A et B.
            scene_location (Optional[Dict[str, str]]): Dictionnaire identifiant le lieu et le sous-lieu.
            context_summary (Optional[str]): Un résumé textuel du contexte général (autres personnages, objets, lore pertinent).
            generation_params (Optional[Dict[str, Any]]): Paramètres additionnels (ex: ton, style)
                                                           qui pourraient modifier le prompt.

        Returns:
            Tuple[str, int]: Le prompt complet et une estimation du nombre de tokens.
        """
        if generation_params is None:
            generation_params = {}

        # Déterminer quel prompt système utiliser
        generate_interaction = generation_params.get("generate_interaction", False)
        dialogue_structure = generation_params.get("dialogue_structure", None)
        current_system_prompt = self._get_interaction_system_prompt() if generate_interaction else self.system_prompt_template
        
        prompt_parts = [current_system_prompt]

        # Section dédiée pour les protagonistes et le lieu
        if scene_protagonists or scene_location:
            prompt_parts.append("\n--- CADRE DE LA SCÈNE ---")
            if scene_protagonists:
                personnage_a = scene_protagonists.get("personnage_a", "Non spécifié")
                personnage_b = scene_protagonists.get("personnage_b", "Non spécifié")
                prompt_parts.append(f"Personnage A (Joueur) : {personnage_a}")
                prompt_parts.append(f"Personnage B (PNJ) : {personnage_b}")
            if scene_location:
                lieu = scene_location.get("lieu", "Non spécifié")
                sous_lieu = scene_location.get("sous_lieu")
                prompt_parts.append(f"Lieu : {lieu}")
                if sous_lieu:
                    prompt_parts.append(f"Sous-Lieu : {sous_lieu}")
        
        if context_summary:
            prompt_parts.append("\n--- CONTEXTE GÉNÉRAL DE LA SCÈNE ---")
            prompt_parts.append(context_summary)
            
        # Ajouter la structure de dialogue si définie (pour les interactions structurées)
        if generate_interaction and dialogue_structure:
            prompt_parts.append("\n--- STRUCTURE DE DIALOGUE REQUISE ---")
            prompt_parts.append(dialogue_structure)
            prompt_parts.append("")
            prompt_parts.append("RÈGLES SPÉCIFIQUES À LA STRUCTURE:")
            prompt_parts.append("• Respecte EXACTEMENT l'ordre et le type d'éléments définis")
            prompt_parts.append("• Personnage A = Joueur (ne parle QUE par les choix, jamais en dialogue direct)")
            prompt_parts.append("• Personnage B = PNJ (parle UNIQUEMENT en dialogue direct, jamais par choix)")
            prompt_parts.append("• 'PNJ' = élément 'dialogue_line' avec Personnage B comme speaker")
            prompt_parts.append("• 'PJ' = élément 'player_choices_block' avec les options du joueur")
            prompt_parts.append("• 'Stop' = fin de l'interaction, aucun élément après")
        
        prompt_parts.append("\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---")
        prompt_parts.append(user_specific_goal)
        
        # Exemple d'utilisation de generation_params (peut être étendu)
        if "tone" in generation_params:
            prompt_parts.append("\n--- TON ATTENDU ---")
            prompt_parts.append(str(generation_params["tone"]))
            
        # Si on génère une interaction, ajouter un rappel sur le format JSON attendu
        if generate_interaction:
            prompt_parts.append("\n--- RAPPEL FORMAT JSON ---")
            prompt_parts.append("Génère uniquement la structure JSON demandée, sans texte d'introduction ni de conclusion.")
            prompt_parts.append("Respecte strictement le format d'Interaction spécifié dans les instructions.")

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

    # Mise à jour de l'appel pour refléter les nouveaux paramètres
    final_prompt, tokens_count = engine.build_prompt(
        user_specific_goal=dummy_user_goal,
        scene_protagonists={"personnage_a": "Elara", "personnage_b": "Gorok"},
        scene_location={"lieu": "Vieille bibliothèque en ruines", "sous_lieu": "Section des grimoires interdits"},
        context_summary=dummy_context, # Pour l'exemple, on garde le contexte général ici
        generation_params=dummy_params
    )
    
    print("\n--- SYSTEM PROMPT UTILISÉ ---")
    print(engine.system_prompt_template)
    print("\n--- PROMPT FINAL GÉNÉRÉ POUR TEST ---")
    print(final_prompt)
    print(f"\n(Estim. tokens: {tokens_count})")

    # Test avec un system prompt personnalisé
    custom_system_prompt = "Tu es un barde facétieux. Raconte une histoire drôle."
    custom_engine = PromptEngine(system_prompt_template=custom_system_prompt)
    custom_prompt, custom_tokens_count = custom_engine.build_prompt(
        user_specific_goal="Le personnage principal glisse sur une peau de banane.",
        scene_protagonists={"personnage_a": "Bardolin", "personnage_b": "Aubergiste Ronchon"},
        scene_location={"lieu": "Taverne du Chardon Rieur"},
        context_summary="Contexte: une taverne animée un soir de fête.",
    )
    print("\n--- TEST AVEC SYSTEM PROMPT PERSONNALISÉ ET NOUVELLE STRUCTURE ---")
    print(custom_prompt)
    print(f"(Estim. tokens: {custom_tokens_count})") 