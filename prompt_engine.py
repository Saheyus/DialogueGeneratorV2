import logging
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
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
                                                    Si None, un prompt par défaut sera chargé depuis la configuration.
        """
        if system_prompt_template is None:
            self.system_prompt_template: str = self._load_default_system_prompt()
        else:
            self.system_prompt_template: str = system_prompt_template

    def _load_default_system_prompt(self) -> str:
        """
        Charge le system prompt par défaut depuis la configuration.
        
        Returns:
            str: Le system prompt par défaut.
        """
        try:
            from services.configuration_service import ConfigurationService
            config_service = ConfigurationService()
            prompt = config_service.get_default_system_prompt()
            if prompt:
                return prompt
        except Exception as e:
            logger.warning(f"Impossible de charger le system prompt depuis la configuration: {e}")
        
        # Fallback: prompt minimal si le chargement échoue
        return "Tu es un dialoguiste expert en jeux de rôle narratifs."

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
            scene_protagonists (Optional[Dict[str, str]]): Dictionnaire identifiant le PJ et le PNJ.
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
                prompt_parts.append(f"PJ : {personnage_a}")
                prompt_parts.append(f"PNJ : {personnage_b}")
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
        
        # Note: Les règles générales (caractérisation, rythme, progression narrative, ton) 
        # sont définies dans le system prompt (system_prompt_template ou system_prompt_override).
        # Elles ne doivent pas être dupliquées ici dans le prompt user.
        # 
        # Hiérarchie des règles :
        # - System prompt : Règles générales (principe de base)
        # - Author profile (ci-dessous) : Préférences de style (modulation)
        # - Scene instructions (dans user_instructions) : Règles spécifiques (prévalent sur les autres)
        
        # Injection vocabulaire et guides narratifs
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
        # Note: Le Structured Output garantit la structure JSON (champs, types), mais pas la logique métier.
        # Ces instructions guident l'IA sur ce que le schéma ne peut pas garantir.
        prompt_parts.append("--- INSTRUCTIONS DE GÉNÉRATION ---")
        prompt_parts.append(
            "**IMPORTANT : Génère UN SEUL nœud de dialogue (un nœud = une réplique du PNJ + choix du joueur).** "
            "Ne génère PAS de séquence de nœuds. Le Structured Output garantit le format, mais tu dois respecter cette logique métier."
        )
        prompt_parts.append("")
        prompt_parts.append("**Règles de contenu :**")
        prompt_parts.append(
            f"- Speaker (qui parle) : {npc_speaker_id} (PNJ interlocuteur)"
        )
        prompt_parts.append(
            f"- Choix (choices) : Options du joueur ({player_character_id})"
        )
        prompt_parts.append(
            "- Tests d'attributs : Format 'AttributeType+SkillId:DD' (ex: 'Raison+Rhétorique:8'). La compétence est obligatoire."
        )
        
        # Instructions sur le nombre de choix
        if max_choices is not None:
            if max_choices == 0:
                prompt_parts.append(
                    "- Ce nœud ne doit PAS avoir de choix (choices). Si le nœud n'a ni line ni choices, il termine le dialogue."
                )
            else:
                prompt_parts.append(
                    f"- Nombre de choix : Entre 1 et {max_choices} selon ce qui est approprié pour la scène."
                )
        else:
            prompt_parts.append(
                "- Nombre de choix : L'IA décide librement entre 2 et 8 choix selon ce qui est approprié pour la scène. Le nœud DOIT avoir au moins 2 choix."
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