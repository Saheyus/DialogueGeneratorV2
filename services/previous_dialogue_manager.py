"""Service de gestion du contexte du dialogue précédent."""
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.context_truncator import ContextTruncator

logger = logging.getLogger(__name__)


class PreviousDialogueManager:
    """Gère le contexte du dialogue précédent pour inclusion dans les prompts.
    
    Responsabilité unique : gestion de l'état et du formatage du dialogue précédent.
    Respecte le principe SRP : uniquement gestion du dialogue précédent.
    """
    
    def __init__(self, context_truncator: Optional['ContextTruncator'] = None):
        """Initialise le gestionnaire de dialogue précédent.
        
        Args:
            context_truncator: Service de troncature pour limiter les tokens (optionnel).
        """
        self._context_truncator = context_truncator
        self._previous_dialogue_context: Optional[str] = None
    
    def set_previous_dialogue_context(self, preview_text: Optional[str]) -> None:
        """Définit le contexte du dialogue précédent (texte formaté Unity JSON).
        
        Args:
            preview_text: Texte formaté généré par preview_unity_dialogue_for_context, ou None pour réinitialiser.
        """
        if preview_text:
            import traceback
            logger.info(
                f"[LOG DEBUG] PreviousDialogueManager: Contexte de dialogue précédent défini (texte formaté Unity JSON). "
                f"Stack: {''.join(traceback.format_stack(limit=5))}"
            )
            self._previous_dialogue_context = preview_text
        else:
            import traceback
            logger.info(
                f"[LOG DEBUG] PreviousDialogueManager: Contexte de dialogue précédent réinitialisé (None). "
                f"Stack: {''.join(traceback.format_stack(limit=5))}"
            )
            self._previous_dialogue_context = None
    
    def format_previous_dialogue_for_context(self, max_tokens_for_history: int) -> str:
        """Formate le dialogue précédent stocké pour l'inclure dans le contexte LLM.
        
        Le texte est déjà formaté (généré par preview_unity_dialogue_for_context),
        on vérifie juste les tokens et tronque si nécessaire.
        
        Args:
            max_tokens_for_history: Nombre maximum de tokens pour le dialogue précédent.
            
        Returns:
            Texte formaté du dialogue précédent, tronqué si nécessaire, ou chaîne vide si aucun dialogue.
        """
        if not self._previous_dialogue_context:
            return ""
        
        if self._context_truncator is None:
            # Si pas de truncator, retourner tel quel (ou logger un warning)
            logger.warning("ContextTruncator non disponible, dialogue précédent retourné sans troncature")
            return self._previous_dialogue_context
        
        return self._context_truncator.format_previous_dialogue(
            self._previous_dialogue_context,
            max_tokens_for_history
        )
    
    @property
    def previous_dialogue_context(self) -> Optional[str]:
        """Récupère le contexte du dialogue précédent (lecture seule)."""
        return self._previous_dialogue_context
