import logging
from typing import Tuple, Optional, Dict, Any, List, Literal
from pathlib import Path
import time
import json
import hashlib
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET
from utils.xml_utils import (
    escape_xml_text,
    parse_xml_element,
    validate_xml_content,
    indent_xml_element,
    create_xml_document,
    extract_text_from_element
)

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
    structured_context: Optional[Any] = None  # PromptStructure optionnel
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
    structured_prompt: Optional[Any] = None  # PromptStructure optionnel

class PromptEngine:
    """
    Gère la construction de prompts pour les modèles de langage.

    Cette classe combine un system prompt, un contexte de scène, et une instruction
    utilisateur pour créer un prompt final optimisé pour la génération de dialogue.
    """
    _last_info_log_time = {}
    _info_log_interval = 5.0
    _tiktoken_warned_models = set()  # Cache des modèles pour lesquels on a déjà warné
    
    # Mapping des modèles personnalisés vers les encodages tiktoken connus
    # Les modèles GPT récents (GPT-4, GPT-4-turbo, etc.) utilisent cl100k_base
    _MODEL_ENCODING_MAP = {
        "gpt-5.2": "cl100k_base",
        "gpt-5.2-thinking": "cl100k_base",
        "gpt-5-mini": "cl100k_base",
        "gpt-5-nano": "cl100k_base",
    }
    def _throttled_info_log(self, log_key: str, message: str):
        now = time.time()
        last_time = PromptEngine._last_info_log_time.get(log_key, 0)
        if now - last_time > PromptEngine._info_log_interval:
            logger.info(message)
            PromptEngine._last_info_log_time[log_key] = now

    def __init__(
        self, 
        system_prompt_template: Optional[str] = None,
        context_builder: Optional[Any] = None,
        vocab_service: Optional[Any] = None,
        guides_service: Optional[Any] = None,
        enricher: Optional[Any] = None
    ) -> None:
        """
        Initialise le PromptEngine.

        Args:
            system_prompt_template (Optional[str]): Un template de system prompt personnalisé.
                                                    Si None, un prompt par défaut sera chargé depuis la configuration.
            context_builder (Optional[ContextBuilder]): Instance de ContextBuilder à utiliser.
                                                       Si None, une instance sera créée quand nécessaire.
            vocab_service (Optional[VocabularyService]): Instance de VocabularyService à utiliser.
                                                        Si None, une instance sera créée quand nécessaire.
            guides_service (Optional[NarrativeGuidesService]): Instance de NarrativeGuidesService à utiliser.
                                                              Si None, une instance sera créée quand nécessaire.
            enricher (Optional[PromptEnricher]): Instance de PromptEnricher à utiliser.
                                                Si None, une instance sera créée avec les services fournis.
        """
        if system_prompt_template is None:
            self.system_prompt_template: str = self._load_default_system_prompt()
        else:
            self.system_prompt_template: str = system_prompt_template
        
        # Stocker le ContextBuilder pour réutilisation (évite les instanciations redondantes)
        self._context_builder: Optional[Any] = context_builder
        
        # Stocker les services pour réutilisation (évite les instanciations redondantes)
        self._vocab_service: Optional[Any] = vocab_service
        self._guides_service: Optional[Any] = guides_service
        
        # Créer PromptEnricher si non fourni
        if enricher is None:
            from services.prompt_enricher import PromptEnricher
            enricher = PromptEnricher(
                vocab_service=self._vocab_service,
                guides_service=self._guides_service
            )
        self._enricher: Optional[Any] = enricher

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
                              Les modèles personnalisés (gpt-5.2, etc.) sont mappés vers cl100k_base.

        Returns:
            int: Le nombre estimé de tokens.
        """
        if tiktoken_available and tiktoken is not None:
            try:
                # Essayer d'abord avec le mapping personnalisé
                encoding_name = self._MODEL_ENCODING_MAP.get(model_name)
                if encoding_name:
                    encoding = tiktoken.get_encoding(encoding_name)
                else:
                    # Essayer avec encoding_for_model pour les modèles standards
                    encoding = tiktoken.encoding_for_model(model_name)
                return len(encoding.encode(text))
            except Exception as e:
                # Warn seulement une fois par modèle pour éviter le spam
                if model_name not in PromptEngine._tiktoken_warned_models:
                    logger.warning(
                        f"Erreur lors du comptage des tokens avec tiktoken pour le modèle {model_name}: {e}. "
                        f"Repli sur le comptage de mots. (Ce warning ne s'affichera qu'une fois par modèle)"
                    )
                    PromptEngine._tiktoken_warned_models.add(model_name)
                pass # Tomber vers le comptage de mots
        
        # Fallback si tiktoken n'est pas disponible ou a échoué
        return len(text.split())


    def _escape_xml(self, text: str) -> str:
        """Échappe les caractères spéciaux XML dans un texte.
        
        DEPRECATED: Utiliser utils.xml_utils.escape_xml_text() directement.
        Cette méthode est conservée pour compatibilité mais délègue à xml_utils.
        
        Args:
            text: Texte à échapper.
            
        Returns:
            Texte échappé pour inclusion dans XML.
        """
        return escape_xml_text(text)

    def _text_to_xml_content(self, text: str) -> str:
        """Convertit un texte en contenu XML, en préservant les sauts de ligne.
        
        DEPRECATED: Utiliser utils.xml_utils.escape_xml_text() directement.
        
        Args:
            text: Texte à convertir.
            
        Returns:
            Texte échappé avec sauts de ligne préservés.
        """
        return escape_xml_text(text) if text else ""


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
    
    def _build_contract_section(self, input: PromptInput) -> Optional[ET.Element]:
        """Construit la section <contract> directement en XML.
        
        Args:
            input: Objet PromptInput contenant les paramètres.
            
        Returns:
            Élément XML <contract> ou None si la section est vide.
        """
        contract_elem = ET.Element("contract")
        has_content = False
        
        # DIRECTIVES D'AUTEUR (GLOBAL)
        if input.author_profile and input.author_profile.strip():
            author_elem = ET.SubElement(contract_elem, "author_directives")
            author_elem.text = escape_xml_text(input.author_profile)
            has_content = True
        
        # TON NARRATIF
        if input.narrative_tags and len(input.narrative_tags) > 0:
            tags_text = ", ".join([f"#{tag}" for tag in input.narrative_tags])
            if tags_text.strip():
                tone_elem = ET.SubElement(contract_elem, "narrative_tone")
                tone_elem.text = escape_xml_text(f"Ton : {tags_text}. Adapte le style, le rythme et l'intensité émotionnelle en fonction de ces tags.")
                has_content = True
        
        # RÈGLES DE PRIORITÉ (toujours présentes car essentielles)
        priority_text = "En cas de conflit entre les instructions, l'ordre de priorité est :\n1. Instructions de scène (SECTION 3) - prévalent sur tout\n2. Directives d'auteur (SECTION 0) - modulent le style global\n3. System prompt - règles générales de base"
        if priority_text.strip():
            priority_elem = ET.SubElement(contract_elem, "priority_rules")
            priority_elem.text = escape_xml_text(priority_text)
            has_content = True
        
        # FORMAT DE SORTIE / INTERDICTIONS (toujours présentes car essentielles)
        format_text = "**IMPORTANT : Génère UN SEUL nœud de dialogue (un nœud = une réplique du PNJ + choix du joueur).**\nNe génère PAS de séquence de nœuds. Le Structured Output garantit le format JSON, mais tu dois respecter cette logique métier."
        if format_text.strip():
            format_elem = ET.SubElement(contract_elem, "output_format")
            format_elem.text = escape_xml_text(format_text)
            has_content = True
        
        # Ne retourner que si au moins un élément a du contenu
        return contract_elem if has_content else None
    
    def _build_technical_section(self, input: PromptInput) -> Optional[ET.Element]:
        """Construit la section <technical> directement en XML.
        
        Args:
            input: Objet PromptInput contenant les paramètres.
            
        Returns:
            Élément XML <technical> ou None si la section est vide.
        """
        technical_elem = ET.Element("technical")
        has_content = False
        
        # INSTRUCTIONS DE GÉNÉRATION
        gen_elem = ET.SubElement(technical_elem, "generation_instructions")
        gen_parts = [
            "Règles de contenu :",
            f"- Speaker (qui parle) : {input.npc_speaker_id} (PNJ interlocuteur)",
            f"- Choix (choices) : Options du joueur ({input.player_character_id})",
            "- Tests d'attributs : Format 'AttributeType+SkillId:DD' (ex: 'Raison+Rhétorique:8'). La compétence est obligatoire."
        ]
        
        # Instructions sur le nombre de choix
        if input.choices_mode == "capped" and input.max_choices is not None:
            if input.max_choices == 0:
                gen_parts.append("- Ce nœud ne doit PAS avoir de choix (choices). Si le nœud n'a ni line ni choices, il termine le dialogue.")
            else:
                gen_parts.append(f"- Nombre de choix : Entre 1 et {input.max_choices} selon ce qui est approprié pour la scène.")
        else:
            gen_parts.append("- Nombre de choix : L'IA décide librement entre 2 et 8 choix selon ce qui est approprié pour la scène. Le nœud DOIT avoir au moins 2 choix.")
        
        gen_elem.text = escape_xml_text("\n".join(gen_parts))
        has_content = True
        
        # COMPÉTENCES DISPONIBLES
        if input.skills_list:
            skills_elem = ET.SubElement(technical_elem, "available_skills")
            skills_text = ", ".join(input.skills_list[:50])
            if len(input.skills_list) > 50:
                skills_text += f" (et {len(input.skills_list) - 50} autres compétences)"
            skills_content = f"Compétences disponibles: {skills_text}\nUtilise ces compétences dans les tests d'attributs (format: 'AttributeType+NomCompétence:DD')."
            skills_elem.text = escape_xml_text(skills_content)
            has_content = True
        
        # TRAITS DISPONIBLES
        if input.traits_list:
            traits_elem = ET.SubElement(technical_elem, "available_traits")
            traits_text = ", ".join(input.traits_list[:30])
            if len(input.traits_list) > 30:
                traits_text += f" (et {len(input.traits_list) - 30} autres traits)"
            traits_content = f"Traits disponibles: {traits_text}\nUtilise ces traits dans traitRequirements des choix (format: [{{'trait': 'NomTrait', 'minValue': 5}}]).\nLes traits peuvent être positifs (ex: 'Courageux') ou négatifs (ex: 'Lâche')."
            traits_elem.text = escape_xml_text(traits_content)
            has_content = True
        
        return technical_elem if has_content else None
    
    def _build_context_section(self, input: PromptInput) -> Optional[ET.Element]:
        """Construit la section <context> directement en XML.
        
        Args:
            input: Objet PromptInput contenant les paramètres.
            
        Returns:
            Élément XML <context> ou None si la section est vide.
        """
        # Si on a un contexte structuré, utiliser serialize_context_to_xml
        if input.structured_context:
            try:
                # Utiliser le ContextBuilder injecté ou en créer un si nécessaire
                if self._context_builder is None:
                    from context_builder import ContextBuilder
                    self._context_builder = ContextBuilder()
                
                # serialize_to_xml retourne maintenant directement un ET.Element
                context_root = self._context_builder._context_serializer.serialize_to_xml(input.structured_context)
                
                if context_root is None:
                    raise ValueError("serialize_context_to_xml a retourné None")
                
                # Valider que c'est bien un élément <context>
                if context_root.tag != "context":
                    logger.warning(f"Élément XML inattendu: {context_root.tag}, attendu 'context'")
                    raise ValueError(f"Tag XML inattendu: {context_root.tag}")
                
                return context_root
            except Exception as e:
                logger.error(
                    f"Erreur lors de la conversion du contexte structuré en XML: {e}. "
                    f"Type d'erreur: {type(e).__name__}. "
                    f"Le système nécessite structured_context pour fonctionner correctement.",
                    exc_info=True
                )
                # Lever une exception claire plutôt que de fallback
                raise ValueError(
                    f"Impossible de sérialiser le contexte structuré en XML: {e}"
                ) from e
        
        # Si pas de structured_context, vérifier si on a au moins un lieu de scène
        # (certains cas peuvent ne pas nécessiter de contexte GDD)
        if input.scene_location:
            context_elem = ET.Element("context")
            location_elem = ET.SubElement(context_elem, "location")
            lieu = input.scene_location.get("lieu", "Non spécifié")
            sous_lieu = input.scene_location.get("sous_lieu")
            location_text = f"Lieu : {lieu}"
            if sous_lieu:
                location_text += f"\nSous-Lieu : {sous_lieu}"
            location_elem.text = escape_xml_text(location_text)
            return context_elem
        
        # Aucun contexte disponible
        return None
    
    def _build_narrative_guides_xml(self, guides_text: str) -> ET.Element:
        """Parse le texte des guides narratifs et crée une structure XML.
        
        Args:
            guides_text: Texte formaté des guides (format Markdown simplifié).
            
        Returns:
            Élément XML <narrative_guides> avec structure hiérarchique.
        """
        guides_elem = ET.Element("narrative_guides")
        
        if not guides_text or not guides_text.strip():
            return guides_elem
        
        lines = guides_text.split('\n')
        current_section = None
        current_subsection = None
        current_content = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Détecter les sections principales
            if line.startswith("--- GUIDE DES DIALOGUES ---"):
                if current_section is not None and current_content:
                    # Finaliser la section précédente
                    if current_subsection is not None:
                        current_subsection.text = escape_xml_text("\n".join(current_content))
                    current_content = []
                
                current_section = ET.SubElement(guides_elem, "dialogue_guide")
                current_subsection = None
                i += 1
                continue
            elif line.startswith("--- GUIDE DE NARRATION ---"):
                if current_section is not None and current_content:
                    # Finaliser la section précédente
                    if current_subsection is not None:
                        current_subsection.text = escape_xml_text("\n".join(current_content))
                    current_content = []
                
                current_section = ET.SubElement(guides_elem, "narrative_guide")
                current_subsection = None
                i += 1
                continue
            elif line.startswith("--- RÈGLES CLÉS EXTRAITES ---"):
                if current_section is not None and current_content:
                    # Finaliser la section précédente
                    if current_subsection is not None:
                        current_subsection.text = escape_xml_text("\n".join(current_content))
                    current_content = []
                
                current_section = ET.SubElement(guides_elem, "extracted_rules")
                current_subsection = None
                i += 1
                continue
            
            # Détecter les sous-sections dans le guide des dialogues
            if current_section is not None and current_section.tag == "dialogue_guide":
                if line.startswith("# ") or line.startswith("## "):
                    # Titre de sous-section
                    if current_subsection is not None and current_content:
                        current_subsection.text = escape_xml_text("\n".join(current_content))
                        current_content = []
                    
                    # Extraire le titre (enlever # et espaces)
                    title = line.lstrip("# ").strip()
                    # Mapper vers des tags sémantiques
                    title_lower = title.lower()
                    if "habillage" in title_lower:
                        tag = "habillage"
                    elif "technique" in title_lower:
                        tag = "technique"
                    elif "interactivité" in title_lower or "interactivite" in title_lower:
                        tag = "interactivity"
                    else:
                        tag = title_lower.replace(" ", "_").replace("é", "e")
                    
                    current_subsection = ET.SubElement(current_section, tag)
                    i += 1
                    continue
                elif line.startswith("TON:") or line.startswith("STRUCTURE:") or line.startswith("INTERDITS:"):
                    # Sous-section dans extracted_rules
                    if current_subsection is not None and current_content:
                        current_subsection.text = escape_xml_text("\n".join(current_content))
                        current_content = []
                    
                    rule_type = line.rstrip(":").lower()
                    current_subsection = ET.SubElement(current_section, rule_type)
                    i += 1
                    continue
            
            # Ajouter le contenu à la sous-section courante ou à la section
            if line or current_content:  # Garder les lignes vides si on a déjà du contenu
                if current_subsection is not None:
                    current_content.append(lines[i])  # Garder l'original avec espaces
                elif current_section is not None:
                    # Pas de sous-section, ajouter directement à la section
                    if not current_content:
                        current_content = []
                    current_content.append(lines[i])
            
            i += 1
        
        # Finaliser la dernière section
        if current_subsection is not None and current_content:
            current_subsection.text = escape_xml_text("\n".join(current_content))
        elif current_section is not None and current_content and current_section.tag != "dialogue_guide":
            # Section sans sous-sections, mettre le contenu directement
            current_section.text = escape_xml_text("\n".join(current_content))
        
        return guides_elem
    
    def _build_narrative_guides_section(self, input: PromptInput) -> Optional[ET.Element]:
        """Construit la section <narrative_guides> directement en XML.
        
        Args:
            input: Objet PromptInput contenant les paramètres.
            
        Returns:
            Élément XML <narrative_guides> ou None si la section est vide.
        """
        if not input.include_narrative_guides:
            return None
        
        guides_parts = []
        guides_parts = self._enricher.enrich_with_narrative_guides(guides_parts, input.include_narrative_guides, format_style="unity")
        
        if not guides_parts:
            return None
        
        # Utiliser la nouvelle méthode pour structurer en XML
        guides_text = "\n".join(guides_parts)
        return self._build_narrative_guides_xml(guides_text)
    
    def _build_vocabulary_xml(self, vocab_text: str) -> ET.Element:
        """Parse le texte du vocabulaire et crée une structure XML.
        
        Args:
            vocab_text: Texte formaté du vocabulaire (format "Terme: Définition").
            
        Returns:
            Élément XML <vocabulary> avec structure hiérarchique par niveau de popularité.
        """
        vocab_elem = ET.Element("vocabulary")
        
        if not vocab_text or not vocab_text.strip():
            return vocab_elem
        
        lines = vocab_text.split('\n')
        current_scope = None
        current_scope_level = None
        
        # Mapping des niveaux de popularité vers les valeurs d'attribut
        level_mapping = {
            "mondialement": "mondial",
            "régionalement": "regional",
            "regionalement": "regional",
            "localement": "local",
            "communautaire": "communautaire",
            "occulte": "occulte",
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ignorer les lignes vides et les en-têtes
            if not line or line.startswith("[VOCABULAIRE"):
                i += 1
                continue
            
            # Détecter un niveau de popularité (format "Mondialement:" ou "Mondialement")
            line_lower = line.lower().rstrip(":")
            if line_lower in level_mapping:
                # Finaliser le scope précédent si nécessaire
                if current_scope and current_scope_level:
                    # Le scope est déjà créé, continuer à ajouter des termes
                    pass
                else:
                    # Créer un nouveau scope
                    scope_level = level_mapping[line_lower]
                    current_scope = ET.SubElement(vocab_elem, "scope")
                    current_scope.set("level", scope_level)
                    current_scope_level = scope_level
                i += 1
                continue
            
            # Détecter un terme (format "Terme: Définition")
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    term_name = parts[0].strip()
                    term_definition = parts[1].strip()
                    
                    if term_name:
                        # Si pas de scope actuel, créer un scope par défaut
                        if current_scope is None:
                            current_scope = ET.SubElement(vocab_elem, "scope")
                            current_scope.set("level", "mondial")  # Par défaut
                            current_scope_level = "mondial"
                        
                        # Créer l'élément term
                        term_elem = ET.SubElement(current_scope, "term")
                        term_elem.set("name", escape_xml_text(term_name))
                        if term_definition:
                            term_elem.text = escape_xml_text(term_definition)
            
            i += 1
        
        return vocab_elem
    
    def _build_vocabulary_section(self, input: PromptInput) -> Optional[ET.Element]:
        """Construit la section <vocabulary> directement en XML.
        
        Args:
            input: Objet PromptInput contenant les paramètres.
            
        Returns:
            Élément XML <vocabulary> ou None si la section est vide.
        """
        if not input.vocabulary_config:
            return None
        
        vocab_parts = []
        vocab_parts = self._enricher.enrich_with_vocabulary(vocab_parts, input.vocabulary_config, input.context_summary, format_style="unity")
        
        if not vocab_parts:
            return None
        
        # Utiliser la nouvelle méthode pour structurer en XML
        vocab_text = "\n".join(vocab_parts)
        return self._build_vocabulary_xml(vocab_text)
    
    def _build_scene_instructions_section(self, input: PromptInput) -> Optional[ET.Element]:
        """Construit la section <scene_instructions> directement en XML.
        
        Args:
            input: Objet PromptInput contenant les paramètres.
            
        Returns:
            Élément XML <scene_instructions> ou None si la section est vide.
        """
        if not input.user_instructions or not input.user_instructions.strip():
            return None
        
        scene_elem = ET.Element("scene_instructions")
        scene_elem.set("priority", "high")
        scene_elem.text = escape_xml_text(input.user_instructions)
        
        return scene_elem
    
    def _parse_xml_to_prompt_structure(
        self, 
        xml_root: ET.Element, 
        structured_context: Optional[Any],
        total_tokens: int
    ) -> Optional[Any]:
        """Parse un élément XML <prompt> et le convertit en PromptStructure (JSON).
        
        Args:
            xml_root: Élément XML racine <prompt>.
            structured_context: Contexte structuré existant (PromptStructure) pour la section context.
            total_tokens: Nombre total de tokens du prompt.
            
        Returns:
            PromptStructure complet ou None si le parsing échoue.
        """
        from models.prompt_structure import PromptStructure, PromptSection, PromptMetadata
        from datetime import datetime
        
        try:
            sections = []
            
            # Mapping des balises XML vers les sections
            section_mapping = {
                "contract": ("other", "SECTION 0. CONTRAT GLOBAL"),
                "technical": ("other", "SECTION 1. INSTRUCTIONS TECHNIQUES (NORMATIVES)"),
                "narrative_guides": ("other", "SECTION 2B. GUIDES NARRATIFS"),
                "vocabulary": ("other", "SECTION 2C. VOCABULAIRE ALTEIR"),
                "scene_instructions": ("instruction", "SECTION 3. INSTRUCTIONS DE SCÈNE (PRIORITÉ EFFECTIVE)"),
            }
            
            # Parser chaque section XML
            for child in xml_root:
                tag = child.tag
                
                # Section context : utiliser structured_context si disponible
                if tag == "context":
                    if structured_context:
                        # Chercher la section context dans structured_context
                        context_section = None
                        for section in structured_context.sections:
                            if section.type == "context" and section.categories:
                                context_section = section
                                break
                        
                        if context_section:
                            sections.append(context_section)
                        else:
                            # Fallback : créer une section basique depuis le XML
                            content = extract_text_from_element(child)
                            if content:
                                sections.append(PromptSection(
                                    type="context",
                                    title="SECTION 2A. CONTEXTE GDD",
                                    content=content,
                                    tokenCount=self._count_tokens(content)
                                ))
                    else:
                        # Pas de structured_context : parser le XML
                        content = extract_text_from_element(child)
                        if content:
                            sections.append(PromptSection(
                                type="context",
                                title="SECTION 2A. CONTEXTE GDD",
                                content=content,
                                tokenCount=self._count_tokens(content)
                            ))
                
                # Autres sections : utiliser le mapping
                elif tag in section_mapping:
                    section_type, section_title = section_mapping[tag]
                    content = extract_text_from_element(child)
                    if content:
                        sections.append(PromptSection(
                            type=section_type,
                            title=section_title,
                            content=content,
                            tokenCount=self._count_tokens(content)
                        ))
            
            # Extraire organizationMode de manière sécurisée
            organization_mode = None
            if structured_context and structured_context.metadata:
                org_mode = structured_context.metadata.organizationMode
                if isinstance(org_mode, str):
                    organization_mode = org_mode
            
            # Créer la structure finale
            return PromptStructure(
                sections=sections,
                metadata=PromptMetadata(
                    totalTokens=total_tokens,
                    generatedAt=datetime.now().isoformat(),
                    organizationMode=organization_mode
                )
            )
        except Exception as e:
            logger.warning(f"Erreur lors du parsing XML vers PromptStructure: {e}")
            return None
    
    def build_prompt(self, input: PromptInput) -> BuiltPrompt:
        """Builder unique et pur pour tous les prompts.
        
        Aucune dépendance à OpenAI, aucun side-effect.
        Toutes les injections (vocabulaire, guides, contraintes) sont ici.
        
        Args:
            input: Objet PromptInput contenant tous les paramètres.
            
        Returns:
            BuiltPrompt avec raw_prompt (exact), token_count, sections, prompt_hash.
        """
        # Gérer le contexte structuré ou texte (nécessaire pour _build_context_section)
        structured_context = None
        if input.structured_context:
            structured_context = input.structured_context
        
        # ASSEMBLAGE FINAL EN XML (construction directe)
        root = ET.Element("prompt")
        
        # Section 0 : Contrat global
        contract_elem = self._build_contract_section(input)
        if contract_elem is not None:
            root.append(contract_elem)
        
        # Section 1 : Instructions techniques
        technical_elem = self._build_technical_section(input)
        if technical_elem is not None:
            root.append(technical_elem)
        
        # Section 2A : Contexte GDD
        context_elem = self._build_context_section(input)
        if context_elem is not None:
            root.append(context_elem)
        
        # Section 2B : Guides narratifs
        guides_elem = self._build_narrative_guides_section(input)
        if guides_elem is not None:
            root.append(guides_elem)
        
        # Section 2C : Vocabulaire
        vocab_elem = self._build_vocabulary_section(input)
        if vocab_elem is not None:
            root.append(vocab_elem)
        
        # Section 3 : Instructions de scène
        scene_elem = self._build_scene_instructions_section(input)
        if scene_elem is not None:
            root.append(scene_elem)
        
        # Créer le document XML complet avec déclaration
        full_prompt = create_xml_document(root)
        
        num_tokens = self._count_tokens(full_prompt)
        prompt_hash = hashlib.sha256(full_prompt.encode('utf-8')).hexdigest()
        
        # Parser le XML pour générer structured_prompt (JSON)
        final_structured_prompt = None
        if structured_context:
            try:
                final_structured_prompt = self._parse_xml_to_prompt_structure(root, structured_context, num_tokens)
            except Exception as e:
                logger.warning(f"Erreur lors du parsing XML vers PromptStructure: {e}")
        
        # Valider le XML final
        if not validate_xml_content(full_prompt):
            logger.error("XML invalide généré dans build_prompt()")
            # Capturer les détails précis de l'erreur XML
            xml_error_details = {}
            try:
                xml_content = full_prompt.split('?>', 1)[-1].strip()
                ET.fromstring(xml_content)
            except ET.ParseError as parse_err:
                # Extraire ligne et colonne depuis le message d'erreur (format: "line X, column Y")
                import re
                lineno = None
                offset = None
                msg = str(parse_err)
                logger.error(f"Message d'erreur complet: {repr(msg)}")
                match = re.search(r'line (\d+), column (\d+)', msg)
                if match:
                    lineno = int(match.group(1))
                    offset = int(match.group(2))
                    logger.error(f"Regex match réussi: ligne {lineno}, colonne {offset}")
                elif hasattr(parse_err, 'position') and parse_err.position:
                    lineno, offset = parse_err.position
                elif hasattr(parse_err, 'lineno'):
                    lineno = parse_err.lineno
                    offset = getattr(parse_err, 'offset', None) or getattr(parse_err, 'colno', None)
                else:
                    logger.error(f"Regex match échoué pour: {msg}")
                
                error_line = None
                problematic_char = None
                
                if lineno and offset:
                    lines = xml_content.split('\n')
                    if lineno <= len(lines):
                        error_line = lines[lineno - 1]
                        if offset <= len(error_line):
                            start = max(0, offset - 10)
                            end = min(len(error_line), offset + 10)
                            problematic_char = error_line[start:end]
                
                xml_error_details = {
                    "line": lineno,
                    "column": offset,
                    "error_line": error_line,
                    "problematic_char": problematic_char,
                    "raw_xml_preview": full_prompt[:2000] if len(full_prompt) > 2000 else full_prompt,
                    "raw_xml_length": len(full_prompt)
                }
                
                logger.error(f"Détails de l'erreur XML: {parse_err}")
                logger.error(f"Position: ligne {lineno}, colonne {offset}")
                if error_line:
                    logger.error(f"Ligne problématique: {repr(error_line)}")
                if problematic_char:
                    logger.error(f"Caractère problématique (colonne {offset}): {repr(problematic_char)}")
            except Exception as e:
                logger.error(f"Erreur lors de la validation XML: {e}")
            
            # Créer une exception personnalisée avec les détails XML
            error = ValueError("XML invalide dans le prompt final")
            error.xml_error_details = xml_error_details
            error.raw_xml = full_prompt
            raise error
        
        # sections_content est déprécié mais conservé pour compatibilité (dict vide)
        # Le structured_prompt (JSON) est maintenant la source de vérité
        sections_content = {}
        
        return BuiltPrompt(
            raw_prompt=full_prompt,
            token_count=num_tokens,
            sections=sections_content,
            prompt_hash=prompt_hash,
            structured_prompt=final_structured_prompt
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