"""Service pour suggérer les champs pertinents selon le contexte de génération."""
import logging
from typing import List, Set, Optional
import re

logger = logging.getLogger(__name__)


class FieldSuggestionService:
    """Suggère les champs pertinents selon le type de génération et le contexte."""
    
    # Règles heuristiques pour les suggestions
    SUGGESTION_RULES = {
        "dialogue": {
            "always": [
                "Nom",
                "Dialogue Type",
                "Dialogue Type.Registre de langage du personnage",
                "Dialogue Type.Champs lexicaux utilisés",
                "Dialogue Type.Expressions courantes",
                "Caractérisation.Désir",
                "Caractérisation.Faiblesse",
            ],
            "keywords": {
                "dialogue": ["Dialogue Type", "Registre", "Expressions", "Champs lexicaux"],
                "characterization": ["Caractérisation", "Désir", "Faiblesse", "Compulsion"],
                "relations": ["Relations", "Background.Relations"],
            }
        },
        "action": {
            "always": [
                "Nom",
                "Pouvoirs",
                "Héritage",
                "Compétences",
            ],
            "keywords": {
                "powers": ["Pouvoir", "Héritage", "Compétence", "Capacité"],
                "stats": ["Stat", "Attribut", "Force", "Agilité"],
            }
        },
        "emotional": {
            "always": [
                "Nom",
                "Caractérisation.Désir",
                "Caractérisation.Faiblesse",
                "Caractérisation.Compulsion",
                "Background.Relations",
            ],
            "keywords": {
                "emotion": ["Désir", "Faiblesse", "Compulsion", "Relations", "Émotion"],
                "background": ["Background", "Histoire", "Évènements"],
            }
        },
        "revelation": {
            "always": [
                "Nom",
                "Background.Contexte",
                "Background.Évènements marquants",
                "Arcs Narratifs",
            ],
            "keywords": {
                "background": ["Background", "Histoire", "Contexte", "Évènements"],
                "arcs": ["Arcs Narratifs", "Actions concrètes", "Conséquences"],
            }
        },
    }
    
    def __init__(self):
        """Initialise le service de suggestions."""
        pass
    
    def get_field_suggestions(
        self,
        element_type: str,
        context: Optional[str] = None,
        available_fields: Optional[List[str]] = None
    ) -> List[str]:
        """Suggère les champs pertinents selon le contexte.
        
        Args:
            element_type: Type d'élément ("character", "location", etc.)
            context: Contexte de génération ("dialogue", "action", "emotional", "revelation")
            available_fields: Liste des champs disponibles (si None, suggère tous les champs possibles)
            
        Returns:
            Liste des chemins de champs suggérés.
        """
        suggestions: Set[str] = set()
        
        # Si pas de contexte spécifique, utiliser "dialogue" par défaut
        if not context:
            context = "dialogue"
        
        # Récupérer les règles pour ce contexte
        rules = self.SUGGESTION_RULES.get(context, self.SUGGESTION_RULES["dialogue"])
        
        # Ajouter les champs "always"
        for field in rules.get("always", []):
            if available_fields is None or field in available_fields:
                suggestions.add(field)
        
        # Ajouter les champs correspondant aux mots-clés
        if available_fields:
            for keyword_group, keywords in rules.get("keywords", {}).items():
                for keyword in keywords:
                    for field in available_fields:
                        if keyword.lower() in field.lower():
                            suggestions.add(field)
        else:
            # Si pas de liste disponible, utiliser les patterns
            for keyword_group, keywords in rules.get("keywords", {}).items():
                for keyword in keywords:
                    # Générer des patterns possibles
                    patterns = self._generate_field_patterns(keyword, element_type)
                    suggestions.update(patterns)
        
        # Filtrer selon le type d'élément
        filtered_suggestions = self._filter_by_element_type(list(suggestions), element_type)
        
        logger.debug(f"Suggestions pour {element_type} (contexte: {context}): {len(filtered_suggestions)} champs")
        return sorted(filtered_suggestions)
    
    def _generate_field_patterns(self, keyword: str, element_type: str) -> List[str]:
        """Génère des patterns de champs possibles à partir d'un mot-clé."""
        patterns = []
        
        # Patterns directs
        patterns.append(keyword)
        
        # Patterns avec préfixes communs
        prefixes = {
            "character": ["Caractérisation", "Background", "Dialogue Type"],
            "location": ["Identité", "Géographie", "Éléments de jeu"],
            "item": ["Fonctionnement", "Décourverte", "Besoin de l'intrigue"],
        }
        
        prefix_list = prefixes.get(element_type, [])
        for prefix in prefix_list:
            patterns.append(f"{prefix}.{keyword}")
            patterns.append(f"{prefix}.{keyword.capitalize()}")
        
        return patterns
    
    def _filter_by_element_type(self, fields: List[str], element_type: str) -> List[str]:
        """Filtre les champs selon le type d'élément."""
        # Pour l'instant, on garde tous les champs
        # On pourrait ajouter une logique de filtrage plus stricte ici
        return fields
    
    def is_field_suggested(
        self,
        field_path: str,
        element_type: str,
        context: Optional[str] = None
    ) -> bool:
        """Vérifie si un champ est suggéré pour le contexte donné."""
        suggestions = self.get_field_suggestions(element_type, context)
        return field_path in suggestions
    
    def get_suggestion_reason(
        self,
        field_path: str,
        element_type: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """Retourne la raison pour laquelle un champ est suggéré."""
        if not context:
            context = "dialogue"
        
        rules = self.SUGGESTION_RULES.get(context, {})
        
        # Vérifier si dans "always"
        if field_path in rules.get("always", []):
            return f"Champ essentiel pour les scènes de type '{context}'"
        
        # Vérifier les mots-clés
        field_lower = field_path.lower()
        for keyword_group, keywords in rules.get("keywords", {}).items():
            for keyword in keywords:
                if keyword.lower() in field_lower:
                    return f"Pertinent pour '{keyword_group}' dans les scènes de type '{context}'"
        
        return None

