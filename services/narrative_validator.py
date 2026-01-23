"""Service pour valider la qualité narrative des dialogues générés."""
import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import re

# Interaction et DialogueLineElement supprimés - système obsolète
# Ce service est obsolète et doit être migré pour utiliser Unity JSON si nécessaire

logger = logging.getLogger(__name__)


class NarrativeValidator:
    """Valide la qualité narrative des dialogues générés."""
    
    # Seuils de validation
    MIN_LINE_LENGTH_WORDS = 10  # Minimum de mots par réplique
    MAX_LINE_LENGTH_WORDS = 50  # Maximum de mots par réplique
    REPETITION_THRESHOLD = 3  # Nombre de répétitions d'un mot pour alerter
    
    def __init__(self):
        """Initialise le validateur."""
        pass
    
    # validate_interaction supprimé - système obsolète (Interaction)
    
    def validate_line_length(self, replique: str) -> List[str]:
        """Valide la longueur d'une réplique.
        
        Args:
            replique: Le texte de la réplique.
            
        Returns:
            Liste de warnings (vide si la longueur est appropriée).
        """
        warnings: List[str] = []
        words = replique.split()
        word_count = len(words)
        
        if word_count < self.MIN_LINE_LENGTH_WORDS:
            warnings.append(
                f"Réplique très courte ({word_count} mots) : '{replique[:50]}...' "
                f"(minimum recommandé: {self.MIN_LINE_LENGTH_WORDS} mots)"
            )
        elif word_count > self.MAX_LINE_LENGTH_WORDS:
            warnings.append(
                f"Réplique très longue ({word_count} mots) : '{replique[:50]}...' "
                f"(maximum recommandé: {self.MAX_LINE_LENGTH_WORDS} mots)"
            )
        
        return warnings
    
    # detect_repetitions supprimé - système obsolète (Interaction)
    
    # check_characterization_usage supprimé - système obsolète (Interaction)
    
    # validate_vocabulary_usage supprimé - système obsolète (Interaction)

