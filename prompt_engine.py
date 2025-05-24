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
Ta tâche est de générer un dialogue cohérent avec le contexte fourni et l'instruction utilisateur.
Si une structure de dialogue spécifique est demandée (ex: PNJ suivi d'un choix PJ), respecte cette structure.
"""

    def _get_interaction_system_prompt_reference(self) -> str:
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
6. Chaque phase doit correspondre à UN SEUL élément dans la liste "elements" de l'Interaction.
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
        scene_protagonists: Optional[Dict[str, str]] = None,
        scene_location: Optional[Dict[str, str]] = None,
        context_summary: Optional[str] = None,
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

        # Utiliser le system_prompt de base. Si le client LLM (comme OpenAIClient)
        # reçoit un response_model, il utilisera son propre system_prompt pour le function calling.
        current_system_prompt = self.system_prompt_template
        
        prompt_parts = [current_system_prompt]

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
            
        # La gestion de la structure est déléguée au function calling si response_model est utilisé.
        # On peut garder une instruction narrative simple pour la structure.
        dialogue_structure_narrative = generation_params.get("dialogue_structure_narrative", None)
        if dialogue_structure_narrative: # Ex: "Un PNJ parle, puis le joueur fait un choix."
            prompt_parts.append("\n--- SÉQUENCE NARRATIVE ATTENDUE ---")
            prompt_parts.append(dialogue_structure_narrative)
        
        prompt_parts.append("\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---")
        prompt_parts.append(user_specific_goal)
        
        if "tone" in generation_params:
            prompt_parts.append("\n--- TON ATTENDU ---")
            prompt_parts.append(str(generation_params["tone"]))
            
        # Plus besoin de rappels sur le format JSON si on utilise le function calling.
        # Le client LLM s'en charge via la définition de l'outil.

        full_prompt = "\n".join(prompt_parts)
        num_tokens = self._count_tokens(full_prompt) 
        
        logger.info(f"Prompt construit pour le LLM. Longueur estimée: {num_tokens} tokens.")
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
    dummy_params: Dict[str, Any] = {
        "tone": "Tendu", 
        "dialogue_structure_narrative": "Un PNJ (Gorok) exprime une réticence, puis un autre PNJ (Elara) tente de le persuader."
        }

    # Mise à jour de l'appel pour refléter les nouveaux paramètres
    final_prompt, tokens_count = engine.build_prompt(
        user_specific_goal=dummy_user_goal,
        scene_protagonists={"personnage_a": "Elara (Joueur)", "personnage_b": "Gorok (PNJ)"},
        scene_location={"lieu": "Vieille bibliothèque"},
        context_summary=dummy_context, 
        generation_params=dummy_params
    )
    
    print("\n--- PROMPT FINAL GÉNÉRÉ (EXEMPLE SIMPLIFIÉ) ---")
    print(final_prompt)
    print(f"(Estim. tokens: {tokens_count})")

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