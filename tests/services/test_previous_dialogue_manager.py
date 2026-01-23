"""Tests pour le service PreviousDialogueManager."""
import pytest
from services.previous_dialogue_manager import PreviousDialogueManager
from services.context_truncator import ContextTruncator


@pytest.fixture
def truncator():
    """Truncator de test."""
    return ContextTruncator()


@pytest.fixture
def manager(truncator):
    """Manager de test."""
    return PreviousDialogueManager(context_truncator=truncator)


class TestPreviousDialogueManager:
    """Tests pour PreviousDialogueManager."""
    
    def test_set_previous_dialogue_context(self, manager):
        """Test de définition du contexte du dialogue précédent."""
        manager.set_previous_dialogue_context("Test dialogue context")
        assert manager.previous_dialogue_context == "Test dialogue context"
    
    def test_set_previous_dialogue_context_none(self, manager):
        """Test de réinitialisation du contexte."""
        manager.set_previous_dialogue_context("Test")
        manager.set_previous_dialogue_context(None)
        assert manager.previous_dialogue_context is None
    
    def test_format_previous_dialogue_for_context(self, manager):
        """Test de formatage du dialogue précédent."""
        manager.set_previous_dialogue_context("Test dialogue context")
        formatted = manager.format_previous_dialogue_for_context(1000)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_format_previous_dialogue_for_context_empty(self, manager):
        """Test de formatage sans dialogue précédent."""
        formatted = manager.format_previous_dialogue_for_context(1000)
        assert formatted == ""
    
    def test_format_previous_dialogue_for_context_without_truncator(self):
        """Test de formatage sans truncator."""
        manager = PreviousDialogueManager(context_truncator=None)
        manager.set_previous_dialogue_context("Test dialogue context")
        formatted = manager.format_previous_dialogue_for_context(1000)
        # Devrait retourner le texte tel quel si pas de truncator
        assert formatted == "Test dialogue context"
    
    def test_previous_dialogue_context_property(self, manager):
        """Test de la propriété previous_dialogue_context."""
        manager.set_previous_dialogue_context("Test")
        assert manager.previous_dialogue_context == "Test"
        
        manager.set_previous_dialogue_context(None)
        assert manager.previous_dialogue_context is None
