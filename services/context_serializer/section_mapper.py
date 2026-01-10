"""Mapping des sections et champs vers tags XML sémantiques.

Ce module centralise tous les mappings entre les titres de sections/champs
du GDD et les tags XML sémantiques utilisés dans le prompt.
"""
import logging
from typing import Optional
from services.context_serializer.field_normalizer import FieldNormalizer

logger = logging.getLogger(__name__)


class SectionMapper:
    """Gère les mappings sections → tags XML et champs → catégories.
    
    Centralise la logique de mapping pour assurer la cohérence des tags XML
    générés à partir des structures GDD.
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
    
    def __init__(self, field_normalizer: Optional[FieldNormalizer] = None):
        """Initialise le mapper avec un normaliseur de champs.
        
        Args:
            field_normalizer: Instance de FieldNormalizer à utiliser.
                            Si None, une nouvelle instance sera créée.
        """
        self._field_normalizer = field_normalizer or FieldNormalizer()
    
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
    
    def categorize_field(self, field_label: str) -> tuple[str, str]:
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
        
        # Vérifier si c'est une section structurée (pas un champ métadonnée)
        # Ces sections ne doivent PAS être dans metadata, elles doivent être des sections séparées
        section_tag, _ = self.get_section_tag(field_label)
        if section_tag not in ("informations", "section", "metadata"):
            # C'est une section structurée (introduction, caracterisation, background, etc.)
            # Ne PAS l'ajouter dans metadata - elle sera créée comme section séparée
            # Retourner None pour indiquer qu'il faut ignorer ce champ dans INFORMATIONS
            logger.debug(f"Champ '{field_label}' identifie comme section structuree '{section_tag}', ignore dans INFORMATIONS")
            return (None, None)  # None indique qu'il faut ignorer ce champ
        
        # Par défaut, mettre dans metadata avec tag basé sur le label
        tag = self._field_normalizer.normalize_for_xml_tag(field_label)
        
        return ("metadata", tag)
