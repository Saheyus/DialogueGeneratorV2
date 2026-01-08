"""Service de sérialisation du contexte en XML et texte."""
import json
import logging
import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from utils.xml_utils import escape_xml_text

if TYPE_CHECKING:
    from models.prompt_structure import PromptStructure

logger = logging.getLogger(__name__)


class ContextSerializer:
    """Sérialise une structure PromptStructure en XML ou texte formaté.
    
    Gère la conversion des structures de contexte en formats XML hiérarchiques
    et texte formaté pour le LLM.
    """
    
    # Mapping des titres de sections vers les tags XML sémantiques
    SECTION_TAG_MAP = {
        "identité": "identity",
        "identity": "identity",
        "caractérisation": "characterization",
        "characterization": "characterization",
        "voix": "voice",
        "voice": "voice",
        "style": "voice",  # "voix" et "style" mappent vers "voice"
        "histoire": "background",
        "background": "background",
        "relations": "background",  # "histoire" et "relations" mappent vers "background"
        "mécaniques": "mechanics",
        "mechanics": "mechanics",
        "introduction": "summary",
        "résumé": "summary",
        "summary": "summary",
        "arcs narratifs": "narrative_arcs",
        "arcs_narratifs": "narrative_arcs",
        "narrative_arcs": "narrative_arcs",
        "informations": "identity",  # INFORMATIONS sera déstructuré en sous-sections
        "autres informations": "metadata",  # AUTRES INFORMATIONS sera dans metadata
    }
    
    # Mapping des champs métadonnées vers leurs catégories et tags XML
    METADATA_FIELD_MAP = {
        # Identity fields (informations d'identité de base)
        "nom": ("identity", "name"),
        "alias": ("identity", "alias"),
        "espèce": ("identity", "species"),
        "genre": ("identity", "gender"),
        "âge": ("identity", "age"),
        "langage": ("identity", "language"),
        "archétype littéraire": ("identity", "archetype"),
        
        # Metadata fields (métadonnées de jeu)
        "occupation": ("metadata", "occupation"),
        "sprint": ("metadata", "sprint"),
        "état": ("metadata", "status"),
        "communautés": ("metadata", "communities"),
        "type": ("metadata", "type"),
        "détient": ("metadata", "holds"),
        "scènes": ("metadata", "scenes"),
        "référence visuelle": ("metadata", "visual_reference"),
        "lieux de vie": ("metadata", "living_places"),
        "axe idéologique": ("metadata", "ideological_axis"),
        "réponse au problème moral": ("metadata", "moral_response"),
        
        # Relationship fields
        "relations principales": ("relationships", "main"),
        "relations": ("relationships", "all"),
    }
    
    def get_section_tag(self, section_title: str) -> tuple[str, bool]:
        """Détermine le tag XML pour une section selon son titre.
        
        Args:
            section_title: Titre de la section.
            
        Returns:
            Tuple (tag_xml, is_generic) où :
            - tag_xml: Le tag XML à utiliser
            - is_generic: True si c'est un tag générique (nécessite un attribut title)
        """
        section_title_lower = section_title.lower()
        
        # Détecter les sections "INFORMATIONS" ou titre vide qui doivent être déstructurées
        if not section_title or section_title_lower in ("informations", "autres informations"):
            return "informations", True  # Sera traité spécialement dans serialize_to_xml
        
        # Chercher dans le mapping
        for key, tag in self.SECTION_TAG_MAP.items():
            if key in section_title_lower:
                return tag, False
        
        # Tag générique si non trouvé
        return "section", True
    
    def categorize_metadata_field(self, field_label: str) -> tuple[str, str]:
        """Catégorise un champ métadonnée et retourne sa catégorie et son tag XML.
        
        Args:
            field_label: Label du champ (ex: "Nom", "Alias", "Occupation").
            
        Returns:
            Tuple (category, tag) où :
            - category: "identity", "metadata", ou "relationships"
            - tag: Tag XML à utiliser (ex: "name", "alias", "occupation")
        """
        field_lower = field_label.lower().strip()
        
        # Chercher dans le mapping
        if field_lower in self.METADATA_FIELD_MAP:
            return self.METADATA_FIELD_MAP[field_lower]
        
        # Par défaut, mettre dans metadata avec tag basé sur le label
        # Sanitization complète pour créer un tag XML valide
        tag = field_lower.replace(" ", "_").replace("é", "e").replace("è", "e")
        
        # Normaliser les caractères Unicode (NFKD) pour convertir les caractères accentués
        tag = unicodedata.normalize('NFKD', tag)
        # Supprimer les caractères de combinaison (diacritiques)
        tag = ''.join(c for c in tag if not unicodedata.combining(c))
        
        # Nettoyer le tag pour qu'il soit valide en XML
        tag = re.sub(r'[^a-z0-9_]', '_', tag)
        tag = re.sub(r'_+', '_', tag)
        tag = tag.strip('_')
        if not tag:
            tag = "field"
        elif tag[0].isdigit():
            tag = "field_" + tag
        
        return ("metadata", tag)
    
    def parse_informations_section(self, content: str, parent_elem: ET.Element) -> None:
        """Parse une section "INFORMATIONS" et crée une structure XML hiérarchique.
        
        Parse le format "Label: Valeur\nLabel: Valeur" et crée des éléments XML
        organisés par catégorie (identity, metadata, relationships).
        
        Args:
            content: Contenu de la section "INFORMATIONS" (format texte).
            parent_elem: Élément XML parent où ajouter la structure parsée.
        """
        if not content or not content.strip():
            return
        
        # Structures pour organiser les champs par catégorie
        identity_elem = None
        metadata_elem = None
        relationships_elem = None
        
        # Parser ligne par ligne
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Détecter le format "Label: Valeur"
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field_label = parts[0].strip()
                    field_value = parts[1].strip()
                    
                    if field_label and field_value:
                        # Catégoriser le champ
                        category, tag = self.categorize_metadata_field(field_label)
                        
                        # Créer l'élément de catégorie si nécessaire
                        if category == "identity":
                            if identity_elem is None:
                                identity_elem = ET.SubElement(parent_elem, "identity")
                            target_elem = identity_elem
                        elif category == "relationships":
                            if relationships_elem is None:
                                relationships_elem = ET.SubElement(parent_elem, "relationships")
                            target_elem = relationships_elem
                        else:  # metadata
                            if metadata_elem is None:
                                metadata_elem = ET.SubElement(parent_elem, "metadata")
                            target_elem = metadata_elem
                        
                        # Créer l'élément pour ce champ
                        field_elem = ET.SubElement(target_elem, tag)
                        field_elem.text = escape_xml_text(field_value)
    
    def parse_json_content(self, content: str) -> Optional[Any]:
        """Détecte et parse le contenu JSON si présent.
        
        Args:
            content: Contenu à analyser.
            
        Returns:
            Dict ou List si le contenu est du JSON valide, None sinon.
        """
        if not content or not content.strip():
            return None
        
        content_stripped = content.strip()
        
        # Détecter si c'est du JSON (commence par { ou [)
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            try:
                parsed = json.loads(content_stripped)
                if isinstance(parsed, (dict, list)):
                    logger.debug(f"JSON détecté et parsé avec succès (type: {type(parsed).__name__}, clés: {list(parsed.keys()) if isinstance(parsed, dict) else len(parsed)})")
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"JSON parsing failed: {e}, content preview: {content_stripped[:100]}")
                return None
        
        # Essayer de détecter du JSON même s'il y a du texte avant
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        json_matches = re.findall(json_pattern, content_stripped, re.DOTALL)
        if json_matches:
            for json_match in sorted(json_matches, key=len, reverse=True):
                try:
                    parsed = json.loads(json_match)
                    if isinstance(parsed, (dict, list)):
                        logger.debug(f"JSON détecté dans le contenu (type: {type(parsed).__name__})")
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
    
    def dict_to_xml_elements(
        self, 
        parent_elem: ET.Element, 
        data: Dict[str, Any], 
        tag_mapping: Optional[Dict[str, str]] = None
    ) -> None:
        """Convertit un dict en éléments XML récursivement.
        
        Args:
            parent_elem: Élément XML parent où ajouter les éléments.
            data: Dictionnaire à convertir.
            tag_mapping: Mapping optionnel de clés vers tags XML (ex: {"Faiblesse": "weakness"}).
        """
        if tag_mapping is None:
            tag_mapping = {}
        
        for key, value in data.items():
            # Mapper la clé vers un tag sémantique si disponible
            tag = tag_mapping.get(key, key.lower().replace(" ", "_").replace("é", "e").replace("è", "e"))
            
            # Normaliser les caractères Unicode (NFKD)
            tag = unicodedata.normalize('NFKD', tag)
            tag = ''.join(c for c in tag if not unicodedata.combining(c))
            
            # Nettoyer le tag pour qu'il soit valide en XML
            tag = re.sub(r'[^a-z0-9_]', '_', tag)
            tag = re.sub(r'_+', '_', tag)
            tag = tag.strip('_')
            if not tag:
                tag = "field"
            elif tag[0].isdigit():
                tag = "field_" + tag
            
            # Validation finale
            if not tag or (tag[0].isdigit() and not tag.startswith("field_")):
                tag = "field_" + (tag if tag else "unknown")
            
            if isinstance(value, dict):
                child_elem = ET.SubElement(parent_elem, tag)
                self.dict_to_xml_elements(child_elem, value, tag_mapping)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        item_elem = ET.SubElement(parent_elem, tag)
                        self.dict_to_xml_elements(item_elem, item, tag_mapping)
                    else:
                        item_elem = ET.SubElement(parent_elem, tag)
                        item_elem.text = escape_xml_text(str(item))
            else:
                child_elem = ET.SubElement(parent_elem, tag)
                child_elem.text = escape_xml_text(str(value))
    
    def serialize_to_text(self, prompt_structure: 'PromptStructure') -> str:
        """Sérialise une structure PromptStructure en texte formaté pour le LLM.
        
        Args:
            prompt_structure: Structure JSON du prompt.
            
        Returns:
            Texte formaté avec marqueurs --- ... --- pour compatibilité.
        """
        from models.prompt_structure import PromptSection, ContextCategory, ContextItem
        
        text_parts = []
        
        for section in prompt_structure.sections:
            if section.type == "system_prompt":
                text_parts.append(section.content)
            elif section.type == "context":
                # Ajouter le titre de section si présent
                if section.title:
                    text_parts.append(f"\n--- {section.title} ---")
                
                # Parcourir les catégories
                if section.categories:
                    for category in section.categories:
                        text_parts.append(f"\n--- {category.title} ---")
                        
                        # Parcourir les items de la catégorie
                        for item in category.items:
                            # Marqueur de l'élément
                            text_parts.append(f"--- {item.name} ---")
                            
                            # Parcourir les sections de l'item
                            for item_section in item.sections:
                                text_parts.append(f"--- {item_section.title} ---")
                                text_parts.append(item_section.content)
                                text_parts.append("")  # Ligne vide entre sections
            else:
                # Autres types de sections
                if section.title:
                    text_parts.append(f"\n--- {section.title} ---")
                text_parts.append(section.content)
        
        return "\n".join(text_parts).strip()
    
    def serialize_to_xml(self, prompt_structure: 'PromptStructure') -> ET.Element:
        """Sérialise une structure PromptStructure en XML hiérarchique pour le LLM.
        
        Format XML avec tags sémantiques :
        - <context> : conteneur principal
        - <characters>, <locations>, <items>, etc. : catégories
        - <character>, <location>, etc. : items individuels
        
        Args:
            prompt_structure: Structure JSON du prompt.
            
        Returns:
            Élément XML racine <context> (sans déclaration XML, sans indentation).
            L'indentation sera gérée par create_xml_document() dans prompt_engine.py.
            
        Raises:
            ValueError: Si la structure est invalide ou si la sérialisation échoue.
        """
        from models.prompt_structure import PromptSection, ContextCategory, ContextItem
        
        try:
            # Créer l'élément racine
            root = ET.Element("context")
            
            # Mapper les types de catégories vers les tags XML
            category_tag_map = {
                "characters": "characters",
                "locations": "locations",
                "items": "items",
                "species": "species",
                "communities": "communities",
                "quests": "quests",
            }
            
            # Mapper les types d'items vers les tags XML
            item_tag_map = {
                "characters": "character",
                "locations": "location",
                "items": "item",
                "species": "species",
                "communities": "community",
                "quests": "quest",
            }
            
            # Parcourir les sections du prompt
            for section in prompt_structure.sections:
                if section.type == "context" and section.categories:
                    # Parcourir les catégories de contexte
                    for category in section.categories:
                        category_type = category.type.lower()
                        category_tag = category_tag_map.get(category_type, "category")
                        item_tag = item_tag_map.get(category_type, "item")
                        
                        # Créer l'élément de catégorie
                        category_elem = ET.SubElement(root, category_tag)
                        
                        # Parcourir les items de la catégorie
                        for item in category.items:
                            # Créer l'élément item
                            item_elem = ET.SubElement(category_elem, item_tag)
                            
                            # Ajouter le nom comme attribut ou élément selon le type
                            if item.metadata and "name" in item.metadata:
                                item_elem.set("name", escape_xml_text(str(item.metadata["name"])))
                            
                            # Parcourir les sections de l'item
                            for item_section in item.sections:
                                section_title = item_section.title or ""
                                section_title_lower = section_title.lower()
                                
                                # Détecter les sections "INFORMATIONS" ou titre vide qui doivent être déstructurées
                                if not section_title or section_title_lower in ("informations", "autres informations"):
                                    # Parser la section INFORMATIONS en structure XML hiérarchique
                                    self.parse_informations_section(item_section.content, item_elem)
                                    continue
                                
                                # Déterminer le tag de section selon le titre
                                tag_xml, is_generic = self.get_section_tag(item_section.title)
                                
                                # Vérifier si le contenu est du JSON à déstructurer
                                json_data = self.parse_json_content(item_section.content)
                                
                                if json_data:
                                    logger.debug(f"JSON détecté pour section '{section_title}' (tag: {tag_xml}), déstructuration en cours...")
                                else:
                                    logger.debug(f"Pas de JSON détecté pour section '{section_title}' (tag: {tag_xml}), contenu preview: {item_section.content[:100] if item_section.content else 'None'}")
                                
                                if json_data:
                                    # Déstructurer le JSON en éléments XML
                                    section_elem = ET.SubElement(item_elem, tag_xml)
                                    
                                    # Mapping spécial pour certaines sections
                                    tag_mapping = {}
                                    if tag_xml == "characterization":
                                        tag_mapping = {
                                            "Faiblesse": "weakness",
                                            "Compulsion": "compulsion",
                                            "Désir": "desire",
                                            "Désir Principal": "desire",
                                            "Weakness": "weakness",
                                            "Desire": "desire",
                                        }
                                    elif tag_xml == "summary" or tag_xml == "introduction":
                                        tag_mapping = {
                                            "Résumé de la fiche": "summary",
                                            "Résumé": "summary",
                                        }
                                    elif tag_xml == "background":
                                        tag_mapping = {
                                            "Contexte": "context",
                                            "Apparence": "appearance",
                                            "Relations": "relationships",
                                            "Centres d'intérêt": "interests",
                                        }
                                    elif tag_xml == "narrative_arcs":
                                        tag_mapping = {
                                            "Actions concrètes": "concrete_actions",
                                            "Quêtes annexes": "side_quests",
                                            "Conséquences de la Révélation": "revelation_consequences",
                                        }
                                    
                                    # Gérer les dicts et les listes
                                    try:
                                        if isinstance(json_data, dict):
                                            self.dict_to_xml_elements(section_elem, json_data, tag_mapping)
                                        elif isinstance(json_data, list):
                                            # Pour les listes, créer un élément pour chaque item
                                            for item in json_data:
                                                if isinstance(item, dict):
                                                    self.dict_to_xml_elements(section_elem, item, tag_mapping)
                                                else:
                                                    item_elem = ET.SubElement(section_elem, "item")
                                                    item_elem.text = escape_xml_text(str(item))
                                    except Exception as e:
                                        # En cas d'erreur, logger et ajouter le contenu brut
                                        logger.warning(f"Erreur lors de la déstructuration JSON pour section '{section_title}': {e}")
                                        section_elem.text = escape_xml_text(item_section.content)
                                else:
                                    # Contenu texte normal
                                    section_elem = ET.SubElement(item_elem, tag_xml)
                                    
                                    # Si c'est un tag générique, ajouter l'attribut title
                                    if is_generic:
                                        section_elem.set("title", escape_xml_text(item_section.title))
                                    
                                    # Ajouter le contenu (échappé)
                                    section_elem.text = escape_xml_text(item_section.content)
            
            # Retourner directement l'élément XML (sans indentation, sans conversion en string)
            return root
        except ET.ParseError as e:
            logger.error(
                f"Erreur de parsing XML lors de la sérialisation du contexte: {e}. "
                f"Nombre de sections dans prompt_structure: {len(prompt_structure.sections) if prompt_structure.sections else 0}.",
                exc_info=True
            )
            raise ValueError(f"Erreur de parsing XML lors de la sérialisation: {e}") from e
        except Exception as e:
            # Logger avec contexte supplémentaire
            sections_info = "N/A"
            if prompt_structure and prompt_structure.sections:
                sections_info = f"{len(prompt_structure.sections)} sections"
                context_sections = [s for s in prompt_structure.sections if s.type == "context"]
                if context_sections:
                    categories_info = []
                    for cs in context_sections:
                        if cs.categories:
                            categories_info.extend([f"{cat.type}({len(cat.items)} items)" for cat in cs.categories])
                    if categories_info:
                        sections_info += f", catégories: {', '.join(categories_info[:5])}"
            
            logger.error(
                f"Erreur lors de la sérialisation du contexte en XML: {e}. "
                f"Type d'erreur: {type(e).__name__}. Structure: {sections_info}.",
                exc_info=True
            )
            raise ValueError(f"Erreur lors de la sérialisation du contexte en XML: {e}") from e
