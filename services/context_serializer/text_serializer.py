"""Sérialisation de structures de prompt en format texte.

Ce module gère la conversion des structures PromptStructure en format texte
avec marqueurs pour compatibilité avec le format legacy.
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.prompt_structure import PromptStructure

logger = logging.getLogger(__name__)


class TextSerializer:
    """Sérialise une structure PromptStructure en texte formaté pour le LLM.
    
    Génère un format texte avec marqueurs "--- ... ---" pour compatibilité
    avec le format legacy et lisibilité pour l'humain.
    """
    
    def serialize(self, prompt_structure: 'PromptStructure') -> str:
        """Sérialise une structure PromptStructure en texte formaté pour le LLM.
        
        Args:
            prompt_structure: Structure JSON du prompt.
            
        Returns:
            Texte formaté avec marqueurs --- ... --- pour compatibilité.
            
        Example:
            >>> serializer = TextSerializer()
            >>> text = serializer.serialize(prompt_structure)
            >>> "--- CONTEXTE GDD ---" in text
            True
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
