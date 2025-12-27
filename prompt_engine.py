import logging
from typing import Tuple, Optional, Dict, Any, List
import time

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
    _last_info_log_time = {}
    _info_log_interval = 5.0
    def _throttled_info_log(self, log_key: str, message: str):
        now = time.time()
        last_time = PromptEngine._last_info_log_time.get(log_key, 0)
        if now - last_time > PromptEngine._info_log_interval:
            logger.info(message)
            PromptEngine._last_info_log_time[log_key] = now

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
        Retourne un system prompt par défaut pour la génération de dialogues.

        Ce prompt sert de point de départ et peut être enrichi avec des détails
        sur la structure JSON Unity attendue, des exemples, des instructions sur la gestion
        des conditions (<<if>>), des commandes (<<command>>), le ton, le style RPG, etc.

        Returns:
            str: Le system prompt par défaut.
        """
        return \
"""
Tu es un dialoguiste expert en jeux de rôle narratifs.

RÈGLES DE CARACTÉRISATION :
- Chaque personnage a une voix unique définie dans le contexte (registre, vocabulaire, expressions)
- Si une section "VOIX ET STYLE" est présente dans le contexte, respecte strictement le profil de voix fourni
- Utilise les expressions courantes et champs lexicaux spécifiés pour chaque personnage
- Les répliques doivent révéler la personnalité, pas juste transmettre de l'information
- Si une section "CARACTÉRISATION" est présente, exploite les qualités, défauts, désirs et faiblesses pour enrichir les dialogues

RÈGLES DE RYTHME :
- Varie la longueur des répliques pour créer du rythme
- Les répliques courtes créent de la tension, les longues développent l'émotion
- Évite les monologues trop longs (max 3-4 phrases par réplique)
- Alterne entre répliques courtes et longues pour maintenir l'attention

RÈGLES DE PROGRESSION NARRATIVE :
- Chaque dialogue doit faire avancer l'histoire ou développer les personnages
- Les choix du joueur doivent avoir un impact narratif clair
- Évite les dialogues "filler" qui ne servent à rien
- Chaque réplique doit apporter quelque chose : information, émotion, tension, ou développement de personnage

RÈGLES DE TON :
- Adapte le ton au contexte (lieu, relation, état émotionnel)
- Les dialogues doivent être immersifs et naturels
- Évite les formulations trop "gamey" ou mécaniques
- Utilise le contexte fourni (lieu, relations, historique) pour adapter le ton

IMPORTANT - FORMAT DE SORTIE :
- Génère le dialogue en texte libre narratif, naturel et lisible
- N'utilise PAS le format Yarn (pas de ---title, pas de ===, pas de nœuds Yarn)
- N'utilise PAS de format de balisage spécial (pas de markdown complexe, pas de JSON sauf indication contraire)
- Écris simplement le dialogue comme un texte narratif normal, avec des guillemets pour les répliques si nécessaire
- Indique clairement qui parle (nom du personnage ou indication narrative)
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
Tu es un dialoguiste expert en jeux de rôle narratifs.

RÈGLES DE CARACTÉRISATION :
- Chaque personnage a une voix unique définie dans le contexte (registre, vocabulaire, expressions)
- Si une section "VOIX ET STYLE" est présente dans le contexte, respecte strictement le profil de voix fourni
- Utilise les expressions courantes et champs lexicaux spécifiés pour chaque personnage
- Les répliques doivent révéler la personnalité, pas juste transmettre de l'information
- Si une section "CARACTÉRISATION" est présente, exploite les qualités, défauts, désirs et faiblesses pour enrichir les dialogues

RÈGLES DE RYTHME :
- Varie la longueur des répliques pour créer du rythme
- Les répliques courtes créent de la tension, les longues développent l'émotion
- Évite les monologues trop longs (max 3-4 phrases par réplique)
- Alterne entre répliques courtes et longues pour maintenir l'attention

RÈGLES DE PROGRESSION NARRATIVE :
- Chaque dialogue doit faire avancer l'histoire ou développer les personnages
- Les choix du joueur doivent avoir un impact narratif clair
- Évite les dialogues "filler" qui ne servent à rien
- Chaque réplique doit apporter quelque chose : information, émotion, tension, ou développement de personnage

RÈGLES DE TON :
- Adapte le ton au contexte (lieu, relation, état émotionnel)
- Les dialogues doivent être immersifs et naturels
- Évite les formulations trop "gamey" ou mécaniques
- Utilise le contexte fourni (lieu, relations, historique) pour adapter le ton

TA TÂCHE :
Générer une interaction structurée au format JSON cohérente avec le contexte fourni (personnages, lieu, quête).
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

RÈGLES TECHNIQUES À SUIVRE:
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
        generation_params: Optional[Dict[str, Any]] = None,
        vocabulary_min_importance: Optional[str] = None,
        include_narrative_guides: bool = True
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
            vocabulary_min_importance (Optional[str]): Niveau d'importance minimum pour le vocabulaire ("Majeur", "Important", etc.).
            include_narrative_guides (bool): Si True, inclut les guides narratifs dans le prompt.

        Returns:
            Tuple[str, int]: Le prompt complet et une estimation du nombre de tokens.
        """
        if generation_params is None:
            generation_params = {}

        # Utiliser le system_prompt de base. Si le client LLM (comme OpenAIClient)
        # reçoit un response_model, il utilisera son propre system_prompt pour le function calling.
        current_system_prompt = self.system_prompt_template
        
        prompt_parts = [current_system_prompt]
        
        # Injection vocabulaire et guides narratifs (après le system prompt de base)
        if vocabulary_min_importance:
            try:
                from services.vocabulary_service import VocabularyService
                vocab_service = VocabularyService()
                all_terms = vocab_service.load_vocabulary()
                if all_terms:
                    filtered_terms = vocab_service.filter_by_importance(all_terms, vocabulary_min_importance)
                    vocab_text = vocab_service.format_for_prompt(filtered_terms)
                    if vocab_text:
                        prompt_parts.append("\n" + vocab_text)
            except Exception as e:
                logger.warning(f"Erreur lors de l'injection du vocabulaire: {e}")
        
        if include_narrative_guides:
            try:
                from services.narrative_guides_service import NarrativeGuidesService
                guides_service = NarrativeGuidesService()
                guides = guides_service.load_guides()
                if guides.get("dialogue_guide") or guides.get("narrative_guide"):
                    guides_text = guides_service.format_for_prompt(guides, include_rules=True)
                    if guides_text:
                        prompt_parts.append("\n" + guides_text)
            except Exception as e:
                logger.warning(f"Erreur lors de l'injection des guides narratifs: {e}")

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
        
        if user_specific_goal and user_specific_goal.strip():
            prompt_parts.append("\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---")
            prompt_parts.append(user_specific_goal)
        
        if "tone" in generation_params:
            prompt_parts.append("\n--- TON ATTENDU ---")
            prompt_parts.append(str(generation_params["tone"]))
        
        # Tags narratifs pour guider le ton
        narrative_tags = generation_params.get("narrative_tags", [])
        if narrative_tags:
            prompt_parts.append("\n--- TON NARRATIF ---")
            tags_text = ", ".join([f"#{tag}" for tag in narrative_tags])
            prompt_parts.append(
                f"Le dialogue doit avoir un ton {tags_text}. "
                f"Adapte le style, le rythme et l'intensité émotionnelle en fonction de ces tags."
            )
        
        # Pour les générations de texte libre (non structurées), rappeler le format attendu
        structured_output = generation_params.get("structured_generation_request", False)
        if not structured_output:
            prompt_parts.append("\n--- FORMAT DE SORTIE ATTENDU ---")
            prompt_parts.append("Génère le dialogue en texte libre narratif. N'utilise PAS le format Yarn (pas de ---title, pas de ===). Écris simplement le dialogue naturellement avec des répliques claires et des indications de qui parle.")
            
        # Plus besoin de rappels sur le format JSON si on utilise le function calling.
        # Le client LLM s'en charge via la définition de l'outil.

        full_prompt = "\n".join(prompt_parts)
        num_tokens = self._count_tokens(full_prompt) 
        
        self._throttled_info_log('prompt_llm', f"Prompt construit pour le LLM. Longueur estimée: {num_tokens} tokens.")
        return full_prompt, num_tokens
    
    def build_unity_dialogue_prompt(
        self,
        user_instructions: str,
        npc_speaker_id: str,
        player_character_id: str = "URESAIR",
        skills_list: Optional[List[str]] = None,
        traits_list: Optional[List[str]] = None,
        context_summary: Optional[str] = None,
        scene_location: Optional[Dict[str, str]] = None,
        max_choices: Optional[int] = None,
        narrative_tags: Optional[List[str]] = None,
        author_profile: Optional[str] = None,
        vocabulary_min_importance: Optional[str] = None,
        include_narrative_guides: bool = True
    ) -> Tuple[str, int]:
        """Construit le prompt pour génération Unity JSON.
        
        Args:
            user_instructions: Instructions spécifiques de l'utilisateur.
            npc_speaker_id: ID du PNJ interlocuteur.
            player_character_id: ID du personnage joueur (par défaut "URESAIR").
            skills_list: Liste des compétences disponibles (optionnel).
            traits_list: Liste des labels de traits disponibles (optionnel).
            context_summary: Résumé du contexte GDD (optionnel).
            scene_location: Dictionnaire du lieu de la scène (optionnel).
            max_choices: Nombre maximum de choix à générer (0-8, ou None pour laisser l'IA décider).
            narrative_tags: Tags narratifs pour guider le ton (optionnel).
            author_profile: Profil d'auteur global (optionnel).
            vocabulary_min_importance: Niveau d'importance minimum pour le vocabulaire (optionnel).
            include_narrative_guides: Si True, inclut les guides narratifs (défaut: True).
            
        Returns:
            Tuple contenant le prompt complet et une estimation du nombre de tokens.
        """
        prompt_parts = []
        
        # Guidance narrative (avant les instructions techniques)
        prompt_parts.append("--- GUIDANCE NARRATIVE ---")
        prompt_parts.append(
            "Tu es un dialoguiste expert en jeux de rôle narratifs. "
            "Génère des dialogues immersifs et naturels qui font avancer l'histoire."
        )
        prompt_parts.append(
            "RÈGLES DE CARACTÉRISATION : "
            "Si une section 'VOIX ET STYLE' est présente dans le contexte, respecte strictement le profil de voix fourni "
            "(registre, vocabulaire, expressions courantes). Les répliques doivent révéler la personnalité du personnage."
        )
        prompt_parts.append(
            "RÈGLES DE RYTHME : "
            "Varie la longueur des répliques (courtes pour la tension, longues pour l'émotion). "
            "Évite les monologues trop longs (max 3-4 phrases par réplique)."
        )
        prompt_parts.append(
            "RÈGLES DE PROGRESSION NARRATIVE : "
            "Chaque dialogue doit faire avancer l'histoire ou développer les personnages. "
            "Évite les dialogues 'filler' qui ne servent à rien."
        )
        prompt_parts.append(
            "RÈGLES DE TON : "
            "Adapte le ton au contexte (lieu, relation, état émotionnel). "
            "Les dialogues doivent être immersifs et naturels, pas mécaniques."
        )
        prompt_parts.append("")
        
        # Injection vocabulaire et guides narratifs (après la guidance narrative)
        if vocabulary_min_importance:
            try:
                from services.vocabulary_service import VocabularyService
                vocab_service = VocabularyService()
                all_terms = vocab_service.load_vocabulary()
                if all_terms:
                    filtered_terms = vocab_service.filter_by_importance(all_terms, vocabulary_min_importance)
                    vocab_text = vocab_service.format_for_prompt(filtered_terms)
                    if vocab_text:
                        prompt_parts.append(vocab_text)
                        prompt_parts.append("")
            except Exception as e:
                logger.warning(f"Erreur lors de l'injection du vocabulaire: {e}")
        
        if include_narrative_guides:
            try:
                from services.narrative_guides_service import NarrativeGuidesService
                guides_service = NarrativeGuidesService()
                guides = guides_service.load_guides()
                if guides.get("dialogue_guide") or guides.get("narrative_guide"):
                    guides_text = guides_service.format_for_prompt(guides, include_rules=True)
                    if guides_text:
                        prompt_parts.append(guides_text)
                        prompt_parts.append("")
            except Exception as e:
                logger.warning(f"Erreur lors de l'injection des guides narratifs: {e}")
        
        # Instructions sur le format Unity JSON
        prompt_parts.append("--- FORMAT DE SORTIE ATTENDU ---")
        prompt_parts.append(
            "**IMPORTANT : Tu dois générer UN SEUL nœud de dialogue, pas une séquence de nœuds.** "
            "Ce nœud contient une réplique du PNJ interlocuteur et les choix de réponse du joueur. "
            "Un nœud = une réplique du PNJ + choix du joueur. Ne génère PAS de séquence de nœuds "
            "(pas de START → NODE_1 → NODE_2...). Si tu génères plusieurs nœuds par erreur, seul le premier sera utilisé."
        )
        prompt_parts.append(
            "Le format sera géré automatiquement via Structured Output, mais voici les règles importantes :"
        )
        prompt_parts.append(
            "- IMPORTANT : Génère un titre descriptif et reconnaissable pour ce dialogue "
            "(ex: 'Rencontre avec le tavernier', 'Discussion sur la quête principale', 'Confrontation avec le bandit'). "
            "Ce titre sera utilisé pour identifier l'interaction, pas dans le dialogue lui-même."
        )
        prompt_parts.append(
            "- Le speaker doit être l'ID du personnage qui parle (contrôlé par l'auteur). "
            "Pour cette génération, le PNJ interlocuteur est : " + npc_speaker_id
        )
        prompt_parts.append(
            "- Le personnage joueur est : " + player_character_id + " (Seigneuresse Uresaïr). "
            "Les choix (choices) sont toujours les options du joueur."
        )
        prompt_parts.append(
            "- Les tests d'attributs utilisent le format : 'AttributeType+SkillId:DD' "
            "(ex: 'Raison+Rhétorique:8'). La compétence est obligatoire."
        )
        prompt_parts.append(
            "- Ne génère PAS d'IDs de nœuds (id, targetNode, successNode, etc.). "
            "Le système les ajoutera automatiquement."
        )
        prompt_parts.append(
            "- Si un nœud n'a ni choices ni nextNode, il termine le dialogue."
        )
        
        # Instructions sur le nombre de choix
        if max_choices is not None:
            if max_choices == 0:
                prompt_parts.append(
                    "- IMPORTANT : Ce nœud ne doit PAS avoir de choix (choices). "
                    "Utilise nextNode pour la navigation linéaire ou laisse vide pour terminer le dialogue."
                )
            else:
                prompt_parts.append(
                    f"- IMPORTANT : Ce nœud doit avoir exactement {max_choices} choix (choices) au maximum. "
                    f"Génère entre 1 et {max_choices} choix selon ce qui est approprié pour la scène."
                )
        else:
            prompt_parts.append(
                "- Tu peux générer des choix (choices) si cela est approprié pour la scène. "
                "Le nombre de choix est libre, mais reste raisonnable (généralement entre 0 et 8 choix). "
                "Si aucun choix n'est nécessaire, utilise nextNode pour la navigation linéaire."
            )
        
        # Liste des compétences disponibles
        if skills_list:
            skills_text = ", ".join(skills_list[:50])  # Limiter à 50 pour éviter un prompt trop long
            if len(skills_list) > 50:
                skills_text += f" (et {len(skills_list) - 50} autres compétences)"
            prompt_parts.append("\n--- COMPÉTENCES DISPONIBLES ---")
            prompt_parts.append(f"Compétences disponibles: {skills_text}")
            prompt_parts.append(
                "Utilise ces compétences dans les tests d'attributs (format: 'AttributeType+NomCompétence:DD')."
            )
        
        # Liste des traits disponibles
        if traits_list:
            traits_text = ", ".join(traits_list[:30])  # Limiter à 30 pour éviter un prompt trop long
            if len(traits_list) > 30:
                traits_text += f" (et {len(traits_list) - 30} autres traits)"
            prompt_parts.append("\n--- TRAITS DISPONIBLES ---")
            prompt_parts.append(f"Traits disponibles: {traits_text}")
            prompt_parts.append(
                "Utilise ces traits dans traitRequirements des choix (format: [{'trait': 'NomTrait', 'minValue': 5}]). "
                "Les traits peuvent être positifs (ex: 'Courageux') ou négatifs (ex: 'Lâche')."
            )
        
        # Contexte de la scène
        if scene_location:
            prompt_parts.append("\n--- LIEU DE LA SCÈNE ---")
            lieu = scene_location.get("lieu", "Non spécifié")
            sous_lieu = scene_location.get("sous_lieu")
            prompt_parts.append(f"Lieu : {lieu}")
            if sous_lieu:
                prompt_parts.append(f"Sous-Lieu : {sous_lieu}")
        
        # Contexte GDD
        if context_summary:
            prompt_parts.append("\n--- CONTEXTE GÉNÉRAL DE LA SCÈNE ---")
            prompt_parts.append(context_summary)
        
        # Profil d'auteur (global, réutilisable)
        if author_profile and author_profile.strip():
            prompt_parts.append("\n--- DIRECTIVES D'AUTEUR (GLOBAL) ---")
            prompt_parts.append(author_profile)
        
        # Instructions utilisateur
        if user_instructions and user_instructions.strip():
            prompt_parts.append("\n--- BRIEF DE SCÈNE (LOCAL) ---")
            prompt_parts.append(user_instructions)
        
        # Tags narratifs pour guider le ton
        if narrative_tags:
            prompt_parts.append("\n--- TON NARRATIF ---")
            tags_text = ", ".join([f"#{tag}" for tag in narrative_tags])
            prompt_parts.append(
                f"Le dialogue doit avoir un ton {tags_text}. "
                f"Adapte le style, le rythme et l'intensité émotionnelle en fonction de ces tags."
            )
        
        full_prompt = "\n".join(prompt_parts)
        num_tokens = self._count_tokens(full_prompt)
        
        self._throttled_info_log('prompt_unity', f"Prompt Unity construit. Longueur estimée: {num_tokens} tokens.")
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