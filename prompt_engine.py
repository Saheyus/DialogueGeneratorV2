import logging
from typing import Tuple, Optional, Dict, Any, List, Literal
from pathlib import Path
import time
import json
import hashlib
from dataclasses import dataclass, asdict

# Essayer d'importer tiktoken, mais continuer si non disponible
try:
    import tiktoken
    tiktoken_available = True
except ImportError:
    tiktoken_available = False
    tiktoken = None # Pour que les références ultérieures ne lèvent pas de NameError

logger = logging.getLogger(__name__)

@dataclass
class PromptInput:
    """Input unifié pour la construction de prompt.
    Contient TOUS les paramètres nécessaires, y compris ceux optionnels.
    """
    user_instructions: str
    npc_speaker_id: str
    player_character_id: str = "URESAIR"
    context_summary: Optional[str] = None
    scene_location: Optional[Dict[str, str]] = None
    author_profile: Optional[str] = None
    narrative_tags: Optional[List[str]] = None
    choices_mode: Literal["free", "capped"] = "free"
    max_choices: Optional[int] = None
    skills_list: Optional[List[str]] = None
    traits_list: Optional[List[str]] = None
    vocabulary_config: Optional[Dict[str, str]] = None
    include_narrative_guides: bool = True

@dataclass
class BuiltPrompt:
    """Résultat de la construction de prompt."""
    raw_prompt: str
    token_count: int
    sections: Dict[str, str]
    prompt_hash: str  # Hash SHA-256 pour validation

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

    def _count_tokens(self, text: str, model_name: str = "gpt-5.2") -> int:
        """
        Compte le nombre de tokens dans un texte en utilisant tiktoken si disponible.

        Si tiktoken n'est pas disponible ou si une erreur se produit,
        un décompte approximatif basé sur les mots (séparés par des espaces) est utilisé.

        Args:
            text (str): Le texte pour lequel compter les tokens.
            model_name (str): Le nom du modèle à utiliser pour l'encodage (par défaut "gpt-5.2").
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

    def _inject_vocabulary(
        self,
        prompt_parts: List[str],
        vocabulary_config: Optional[Dict[str, str]] = None,
        context_text: Optional[str] = None,
        format_style: str = "standard",
        vocab_service: Optional[Any] = None
    ) -> List[str]:
        """Injecte le vocabulaire dans les parties du prompt.
        
        Args:
            prompt_parts: Liste des parties du prompt à enrichir.
            vocabulary_config: Configuration du vocabulaire par niveau (dict avec clés "Mondialement", "Régionalement", etc.
                              et valeurs "all", "auto", "none"). Si None, n'injecte pas de vocabulaire.
            context_text: Texte du contexte pour la détection automatique (requis si un niveau est en mode "auto").
            format_style: Style de formatage ("standard" ou "unity").
            vocab_service: Service de vocabulaire (optionnel, instancié si None).
            
        Returns:
            Liste des parties du prompt enrichie avec le vocabulaire.
        """
        if not vocabulary_config:
            return prompt_parts
        
        if vocab_service is None:
            try:
                from services.vocabulary_service import VocabularyService
                vocab_service = VocabularyService()
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du vocabulaire: {e}")
                return prompt_parts
        
        try:
            all_terms = vocab_service.load_vocabulary()
            if all_terms:
                filtered_terms = vocab_service.filter_by_config(all_terms, vocabulary_config, context_text)
                vocab_text = vocab_service.format_for_prompt(filtered_terms)
                if vocab_text:
                    if format_style == "unity":
                        prompt_parts.append(vocab_text)
                        prompt_parts.append("")
                    else:  # standard
                        prompt_parts.append("\n" + vocab_text)
        except Exception as e:
            logger.warning(f"Erreur lors de l'injection du vocabulaire: {e}")
        
        return prompt_parts

    def _inject_narrative_guides(
        self,
        prompt_parts: List[str],
        include_narrative_guides: bool,
        format_style: str = "standard",
        guides_service: Optional[Any] = None
    ) -> List[str]:
        """Injecte les guides narratifs dans les parties du prompt.
        
        Args:
            prompt_parts: Liste des parties du prompt à enrichir.
            include_narrative_guides: Si True, inclut les guides narratifs.
            format_style: Style de formatage ("standard" ou "unity").
            guides_service: Service de guides narratifs (optionnel, instancié si None).
            
        Returns:
            Liste des parties du prompt enrichie avec les guides narratifs.
        """
        if not include_narrative_guides:
            return prompt_parts
        
        if guides_service is None:
            try:
                from services.narrative_guides_service import NarrativeGuidesService
                guides_service = NarrativeGuidesService()
            except Exception as e:
                logger.warning(f"Erreur lors du chargement des guides: {e}")
                return prompt_parts
        
        try:
            guides = guides_service.load_guides()
            if guides.get("dialogue_guide") or guides.get("narrative_guide"):
                guides_text = guides_service.format_for_prompt(guides, include_rules=True)
                if guides_text:
                    if format_style == "unity":
                        prompt_parts.append(guides_text)
                        prompt_parts.append("")
                    else:  # standard
                        prompt_parts.append("\n" + guides_text)
        except Exception as e:
            logger.warning(f"Erreur lors de l'injection des guides narratifs: {e}")
        
        return prompt_parts

    def _format_tone_section(self, generation_params: Dict[str, Any]) -> Optional[str]:
        """Formate la section ton et style en combinant tone et narrative_tags.
        
        Args:
            generation_params: Dictionnaire contenant les paramètres de génération.
            
        Returns:
            Chaîne formatée pour la section ton et style, ou None si aucun ton n'est défini.
        """
        tone = generation_params.get("tone")
        narrative_tags = generation_params.get("narrative_tags", [])
        
        if not tone and not narrative_tags:
            return None
        
        parts = []
        if tone:
            parts.append(f"Ton général : {tone}")
        if narrative_tags:
            tags_text = ", ".join([f"#{tag}" for tag in narrative_tags])
            parts.append(f"Tags narratifs : {tags_text}")
            parts.append("Adapte le style, le rythme et l'intensité émotionnelle en fonction de ces tags.")
        
        return "\n".join(parts)

    # build_prompt() supprimé - système texte libre obsolète, utiliser build_unity_dialogue_prompt() à la place
    
    def build_prompt(self, input: PromptInput) -> BuiltPrompt:
        """Builder unique et pur pour tous les prompts.
        
        Aucune dépendance à OpenAI, aucun side-effect.
        Toutes les injections (vocabulaire, guides, contraintes) sont ici.
        
        Args:
            input: Objet PromptInput contenant tous les paramètres.
            
        Returns:
            BuiltPrompt avec raw_prompt (exact), token_count, sections, prompt_hash.
        """
        sections_content = {}
        
        # ===================================================================
        # SECTION 0. CONTRAT GLOBAL
        # ===================================================================
        section0_parts = []
        
        # DIRECTIVES D'AUTEUR (GLOBAL)
        if input.author_profile and input.author_profile.strip():
            section0_parts.append("**DIRECTIVES D'AUTEUR (GLOBAL)**")
            section0_parts.append(input.author_profile)
            section0_parts.append("")
        
        # TON NARRATIF (résumé, pas dissertation)
        if input.narrative_tags:
            tags_text = ", ".join([f"#{tag}" for tag in input.narrative_tags])
            section0_parts.append("**TON NARRATIF**")
            section0_parts.append(f"Ton : {tags_text}. Adapte le style, le rythme et l'intensité émotionnelle en fonction de ces tags.")
            section0_parts.append("")
        
        # RÈGLES DE PRIORITÉ
        section0_parts.append("**RÈGLES DE PRIORITÉ**")
        section0_parts.append("En cas de conflit entre les instructions, l'ordre de priorité est :")
        section0_parts.append("1. Instructions de scène (SECTION 3) - prévalent sur tout")
        section0_parts.append("2. Directives d'auteur (SECTION 0) - modulent le style global")
        section0_parts.append("3. System prompt - règles générales de base")
        section0_parts.append("")
        
        # FORMAT DE SORTIE / INTERDICTIONS
        section0_parts.append("**FORMAT DE SORTIE / INTERDICTIONS**")
        section0_parts.append("**IMPORTANT : Génère UN SEUL nœud de dialogue (un nœud = une réplique du PNJ + choix du joueur).**")
        section0_parts.append("Ne génère PAS de séquence de nœuds. Le Structured Output garantit le format JSON, mais tu dois respecter cette logique métier.")
        
        sections_content["SECTION 0"] = "### SECTION 0. CONTRAT GLOBAL\n\n" + "\n".join(section0_parts)
        
        # ===================================================================
        # SECTION 1. INSTRUCTIONS TECHNIQUES (NORMATIVES)
        # ===================================================================
        section1_parts = []
        
        # INSTRUCTIONS DE GÉNÉRATION (techniques Unity)
        section1_parts.append("**INSTRUCTIONS DE GÉNÉRATION**")
        section1_parts.append("Règles de contenu :")
        section1_parts.append(f"- Speaker (qui parle) : {input.npc_speaker_id} (PNJ interlocuteur)")
        section1_parts.append(f"- Choix (choices) : Options du joueur ({input.player_character_id})")
        section1_parts.append("- Tests d'attributs : Format 'AttributeType+SkillId:DD' (ex: 'Raison+Rhétorique:8'). La compétence est obligatoire.")
        
        # Instructions sur le nombre de choix
        if input.choices_mode == "capped" and input.max_choices is not None:
            if input.max_choices == 0:
                section1_parts.append("- Ce nœud ne doit PAS avoir de choix (choices). Si le nœud n'a ni line ni choices, il termine le dialogue.")
            else:
                section1_parts.append(f"- Nombre de choix : Entre 1 et {input.max_choices} selon ce qui est approprié pour la scène.")
        else:
            # Mode "free" par défaut
            section1_parts.append("- Nombre de choix : L'IA décide librement entre 2 et 8 choix selon ce qui est approprié pour la scène. Le nœud DOIT avoir au moins 2 choix.")
        section1_parts.append("")
        
        # COMPÉTENCES DISPONIBLES
        if input.skills_list:
            skills_text = ", ".join(input.skills_list[:50])
            if len(input.skills_list) > 50:
                skills_text += f" (et {len(input.skills_list) - 50} autres compétences)"
            section1_parts.append("--- COMPÉTENCES DISPONIBLES ---")
            section1_parts.append(f"Compétences disponibles: {skills_text}")
            section1_parts.append("Utilise ces compétences dans les tests d'attributs (format: 'AttributeType+NomCompétence:DD').")
            section1_parts.append("")
        
        # TRAITS DISPONIBLES
        if input.traits_list:
            traits_text = ", ".join(input.traits_list[:30])
            if len(input.traits_list) > 30:
                traits_text += f" (et {len(input.traits_list) - 30} autres traits)"
            section1_parts.append("--- TRAITS DISPONIBLES ---")
            section1_parts.append(f"Traits disponibles: {traits_text}")
            section1_parts.append("Utilise ces traits dans traitRequirements des choix (format: [{'trait': 'NomTrait', 'minValue': 5}]).")
            section1_parts.append("Les traits peuvent être positifs (ex: 'Courageux') ou négatifs (ex: 'Lâche').")
            section1_parts.append("")
            
        sections_content["SECTION 1"] = "### SECTION 1. INSTRUCTIONS TECHNIQUES (NORMATIVES)\n\n" + "\n".join(section1_parts)
        
        # ===================================================================
        # SECTION 2A. CONTEXTE GDD (personnages, lieux, objets)
        # ===================================================================
        section2a_parts = []
        if input.context_summary:
            # FIX: Retirer le vocabulaire du contexte s'il y est (déjà géré dans l'ancienne logique)
            cleaned_context = input.context_summary
            if "[VOCABULAIRE ALTEIR]" in input.context_summary:
                vocab_start = input.context_summary.find("[VOCABULAIRE ALTEIR]")
                if vocab_start == 0 or (vocab_start > 0 and input.context_summary[:vocab_start].strip() == ""):
                    next_section = input.context_summary.find("\n---", vocab_start)
                    if next_section == -1: next_section = input.context_summary.find("\n###", vocab_start)
                    if next_section != -1:
                        cleaned_context = input.context_summary[next_section:].lstrip()
            
            section2a_parts.append("**CONTEXTE GÉNÉRAL DE LA SCÈNE**")
            section2a_parts.append(cleaned_context)
            section2a_parts.append("")
            
        # LIEU DE LA SCÈNE
        if input.scene_location:
            lieu = input.scene_location.get("lieu", "Non spécifié")
            sous_lieu = input.scene_location.get("sous_lieu")
            section2a_parts.append("**LIEU DE LA SCÈNE**")
            section2a_parts.append(f"Lieu : {lieu}")
            if sous_lieu:
                section2a_parts.append(f"Sous-Lieu : {sous_lieu}")
                
        if section2a_parts:
            sections_content["SECTION 2A"] = "### SECTION 2A. CONTEXTE GDD\n\n" + "\n".join(section2a_parts)
            
        # ===================================================================
        # SECTION 2B. GUIDES NARRATIFS
        # ===================================================================
        guides_parts = []
        guides_parts = self._inject_narrative_guides(guides_parts, input.include_narrative_guides, format_style="unity")
        if guides_parts:
            sections_content["SECTION 2B"] = "### SECTION 2B. GUIDES NARRATIFS\n\n" + "\n".join(guides_parts)
            
        # ===================================================================
        # SECTION 2C. VOCABULAIRE ALTEIR
        # ===================================================================
        vocab_parts = []
        vocab_parts = self._inject_vocabulary(vocab_parts, input.vocabulary_config, input.context_summary, format_style="unity")
        if vocab_parts:
            sections_content["SECTION 2C"] = "### SECTION 2C. VOCABULAIRE ALTEIR\n\n" + "\n".join(vocab_parts)
            
        # ===================================================================
        # SECTION 3. INSTRUCTIONS DE SCÈNE (PRIORITÉ EFFECTIVE)
        # ===================================================================
        section3_parts = []
        if input.user_instructions and input.user_instructions.strip():
            section3_parts.append("**BRIEF DE SCÈNE (LOCAL)**")
            section3_parts.append(input.user_instructions)
            
        if section3_parts:
            sections_content["SECTION 3"] = "### SECTION 3. INSTRUCTIONS DE SCÈNE (PRIORITÉ EFFECTIVE)\n\n" + "\n".join(section3_parts)
            
        # ASSEMBLLAGE FINAL
        all_parts = []
        # Ordre strict des sections
        order = ["SECTION 0", "SECTION 1", "SECTION 2A", "SECTION 2B", "SECTION 2C", "SECTION 3"]
        for key in order:
            if key in sections_content:
                all_parts.append(sections_content[key])
                all_parts.append("")
                all_parts.append("---")
                all_parts.append("")
                
        full_prompt = "\n".join(all_parts).strip()
        num_tokens = self._count_tokens(full_prompt)
        prompt_hash = hashlib.sha256(full_prompt.encode('utf-8')).hexdigest()
        
        return BuiltPrompt(
            raw_prompt=full_prompt,
            token_count=num_tokens,
            sections=sections_content,
            prompt_hash=prompt_hash
        )

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
        vocabulary_config: Optional[Dict[str, str]] = None,
        include_narrative_guides: bool = True
    ) -> Tuple[str, int]:
        """DEPRECATED: Utiliser build_prompt(PromptInput) à la place.
        """
        # Mapper vers PromptInput
        prompt_input = PromptInput(
            user_instructions=user_instructions,
            npc_speaker_id=npc_speaker_id,
            player_character_id=player_character_id,
            skills_list=skills_list,
            traits_list=traits_list,
            context_summary=context_summary,
            scene_location=scene_location,
            max_choices=max_choices,
            choices_mode="capped" if max_choices is not None else "free",
            narrative_tags=narrative_tags,
            author_profile=author_profile,
            vocabulary_config=vocabulary_config,
            include_narrative_guides=include_narrative_guides
        )
        
        built = self.build_prompt(prompt_input)
        return built.raw_prompt, built.token_count

# Tests build_prompt() supprimés - système texte libre obsolète
# Utiliser build_unity_dialogue_prompt() pour les tests à la place 