"""Service pour organiser intelligemment les sections du contexte dans le prompt."""
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContextOrganizer:
    """Organise les champs du contexte en sections logiques pour le prompt."""
    
    # Ordre des sections pour le mode "narrative"
    NARRATIVE_SECTIONS = [
        "identity",
        "characterization",
        "voice",
        "background",
        "mechanics",
    ]
    
    # Labels des sections
    SECTION_LABELS = {
        "identity": "IDENTITÉ",
        "characterization": "CARACTÉRISATION",
        "voice": "VOIX ET STYLE",
        "background": "HISTOIRE ET RELATIONS",
        "mechanics": "MÉCANIQUES",
    }
    
    # Champs essentiels distincts (2 critères indépendants) :
    # - ESSENTIAL_CONTEXT_FIELDS : champs essentiels du CONTEXTE NARRATIF (après "Introduction")
    # - ESSENTIAL_METADATA_FIELDS : champs essentiels des MÉTADONNÉES (avant "Introduction")
    #
    # IMPORTANT: un champ peut être "métadonnée" et "essentiel", ou "contexte" et "essentiel".
    # Ces listes ne définissent PAS la frontière métadonnées/contexte (c'est `is_metadata`).
    ESSENTIAL_CONTEXT_FIELDS = {
        "character": [
            # Minimum utile pour écrire une scène/dialogue :
            "Introduction.Résumé de la fiche",
            "Dialogue Type.Registre de langage du personnage",
            "Dialogue Type.Expressions courantes",
            "Caractérisation.Désir",
            "Caractérisation.Faiblesse",
            "Background.Relations",
        ],
        "location": [
            "Introduction.Résumé de la fiche",
        ],
        "item": [
            "Introduction.Résumé de la fiche",
        ],
        "species": [
            "Introduction.Résumé de la fiche",
        ],
        "community": [
            "Introduction.Résumé de la fiche",
        ],
    }

    ESSENTIAL_METADATA_FIELDS = {
        "character": [
            "Nom",
            "Alias",
            "Occupation",
            "Espèce",
        ],
        "location": [
            "Nom",
        ],
        "item": [
            "Nom",
            "Type",
        ],
        "species": [
            "Nom",
            "Type",
        ],
        "community": [
            "Nom",
        ],
    }
    
    def __init__(self):
        """Initialise l'organisateur."""
        pass
    
    def organize_context(
        self,
        element_data: Dict,
        element_type: str,
        fields_to_include: List[str],
        organization_mode: str = "default"
    ) -> str:
        """Organise les champs d'un élément selon le mode d'organisation.
        
        Args:
            element_data: Données complètes de l'élément
            element_type: Type d'élément ("character", "location", etc.)
            fields_to_include: Liste des chemins de champs à inclure
            organization_mode: Mode d'organisation ("default", "narrative", "minimal")
            
        Returns:
            Texte formaté avec les champs organisés.
        """
        if organization_mode == "minimal":
            return self._organize_minimal(element_data, element_type, fields_to_include)
        elif organization_mode == "narrative":
            return self._organize_narrative(element_data, element_type, fields_to_include)
        else:  # default
            return self._organize_default(element_data, element_type, fields_to_include)
    
    def _organize_default(
        self,
        element_data: Dict,
        element_type: str,
        fields_to_include: List[str]
    ) -> str:
        """Organisation par défaut : ordre linéaire des champs."""
        parts = []
        
        for field_path in fields_to_include:
            value = self._extract_field_value(element_data, field_path)
            if value is None:
                continue
            
            label = self._generate_label(field_path)
            formatted_value = self._format_value(value)
            parts.append(f"{label}: {formatted_value}")
        
        return "\n".join(parts)
    
    def _organize_narrative(
        self,
        element_data: Dict,
        element_type: str,
        fields_to_include: List[str]
    ) -> str:
        """Organisation narrative : groupement par sections logiques."""
        # Grouper les champs par catégorie
        fields_by_category = defaultdict(list)
        
        for field_path in fields_to_include:
            category = self._categorize_field(field_path, element_type)
            fields_by_category[category or "other"].append(field_path)
        
        # Construire les sections dans l'ordre défini
        sections = []
        for section_key in self.NARRATIVE_SECTIONS:
            if section_key in fields_by_category:
                section_label = self.SECTION_LABELS.get(section_key, section_key.upper())
                section_fields = fields_by_category[section_key]
                
                section_parts = [f"--- {section_label} ---"]
                for field_path in section_fields:
                    value = self._extract_field_value(element_data, field_path)
                    if value is None:
                        continue
                    
                    label = self._generate_label(field_path)
                    formatted_value = self._format_value(value)
                    section_parts.append(f"{label}: {formatted_value}")
                
                if len(section_parts) > 1:  # Au moins un champ (en plus du titre)
                    sections.append("\n".join(section_parts))
        
        # Ajouter les champs non catégorisés à la fin
        if "other" in fields_by_category:
            other_fields = fields_by_category["other"]
            if other_fields:
                section_parts = ["--- AUTRES INFORMATIONS ---"]
                for field_path in other_fields:
                    value = self._extract_field_value(element_data, field_path)
                    if value is None:
                        continue
                    
                    label = self._generate_label(field_path)
                    formatted_value = self._format_value(value)
                    section_parts.append(f"{label}: {formatted_value}")
                
                sections.append("\n".join(section_parts))
        
        return "\n\n".join(sections)
    
    def _organize_minimal(
        self,
        element_data: Dict,
        element_type: str,
        fields_to_include: List[str]
    ) -> str:
        """Organisation minimale : seulement les champs essentiels."""
        # Filtrer pour ne garder que les champs essentiels
        essential_fields = self.ESSENTIAL_CONTEXT_FIELDS.get(element_type, [])
        
        # Intersection entre fields_to_include et essential_fields
        minimal_fields = [
            f for f in fields_to_include 
            if f in essential_fields or any(essential in f for essential in essential_fields)
        ]
        
        # Si aucun champ essentiel n'est dans la liste, utiliser les premiers champs
        if not minimal_fields:
            minimal_fields = fields_to_include[:5]  # Limiter à 5 champs
        
        return self._organize_default(element_data, element_type, minimal_fields)
    
    def _extract_field_value(self, data: Dict, path: str) -> Optional[any]:
        """Extrait la valeur d'un champ depuis un chemin."""
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _format_value(self, value: any) -> str:
        """Formate une valeur pour l'affichage."""
        if isinstance(value, dict):
            # Pour les dicts, essayer de trouver un résumé ou convertir en JSON
            if "Résumé" in value or "Résumé de la fiche" in value:
                return str(value.get("Résumé") or value.get("Résumé de la fiche", ""))
            # Sinon, convertir en JSON compact
            import json
            return json.dumps(value, ensure_ascii=False, indent=2)
        elif isinstance(value, list):
            # Pour les listes, joindre les éléments
            if not value:
                return "Aucun"
            if isinstance(value[0], dict):
                # Liste de dicts - extraire les noms si possible
                names = [item.get("Nom", item.get("Titre", str(item))) for item in value]
                return ", ".join(names)
            else:
                return ", ".join(str(item) for item in value)
        else:
            return str(value)
    
    def _generate_label(self, path: str) -> str:
        """Génère un label lisible à partir d'un chemin."""
        parts = path.split(".")
        last_part = parts[-1]
        
        # Remplacer les underscores et capitaliser
        label = last_part.replace("_", " ").replace("-", " ")
        label = " ".join(word.capitalize() for word in label.split())
        
        return label
    
    def _categorize_field(self, path: str, element_type: str) -> Optional[str]:
        """Catégorise un champ selon son chemin."""
        path_lower = path.lower()
        
        # Vérifier les catégories spécifiques en premier (priorité)
        if any(kw in path_lower for kw in ["dialogue", "registre", "lexical", "expression", "voix", "langage"]):
            return "voice"
        
        if any(kw in path_lower for kw in ["désir", "faiblesse", "compulsion", "qualité", "défaut"]):
            return "characterization"
        
        if any(kw in path_lower for kw in ["background", "histoire", "contexte", "relation", "évènement", "centre"]):
            return "background"
        
        if any(kw in path_lower for kw in ["pouvoir", "héritage", "compétence", "stat", "attribut", "trait"]):
            return "mechanics"
        
        # Catégories basées sur les mots-clés génériques (en dernier)
        if any(kw in path_lower for kw in ["nom", "alias", "occupation", "type", "rôle", "catégorie"]):
            return "identity"
        
        return None

