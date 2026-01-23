"""Service de mapping des catégories d'éléments vers types et labels."""
from typing import Dict


class ContextMapper:
    """Centralise les mappings de catégories d'éléments vers types et labels.
    
    Fournit des mappings statiques pour convertir les clés de catégories
    (ex: "characters", "locations") vers leurs types d'éléments correspondants
    (ex: "character", "location") et leurs labels pour les marqueurs
    (ex: "PNJ", "LIEU").
    """
    
    # Mapping des catégories vers les types d'éléments
    ELEMENT_TYPE_MAP: Dict[str, str] = {
        "characters": "character",
        "locations": "location",
        "items": "item",
        "species": "species",
        "communities": "community",
    }
    
    # Mapping des catégories vers les labels d'éléments pour les marqueurs
    ELEMENT_LABEL_MAP: Dict[str, str] = {
        "characters": "PNJ",
        "locations": "LIEU",
        "items": "OBJET",
        "species": "ESPÈCE",
        "communities": "COMMUNAUTÉ",
        "quests": "QUÊTE",
    }
    
    @staticmethod
    def get_element_type(category_key: str) -> str:
        """Retourne le type d'élément pour une catégorie.
        
        Args:
            category_key: Clé de catégorie (ex: "characters", "locations").
            
        Returns:
            Type d'élément correspondant (ex: "character", "location").
        """
        return ContextMapper.ELEMENT_TYPE_MAP.get(category_key, category_key)
    
    @staticmethod
    def get_element_label(category_key: str) -> str:
        """Retourne le label d'élément pour les marqueurs explicites.
        
        Args:
            category_key: Clé de catégorie (ex: "characters", "locations").
            
        Returns:
            Label pour les marqueurs (ex: "PNJ", "LIEU").
        """
        return ContextMapper.ELEMENT_LABEL_MAP.get(category_key, category_key.upper())
