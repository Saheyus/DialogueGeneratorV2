"""Tests pour le service FieldSuggestionService."""
import pytest
from services.field_suggestion_service import FieldSuggestionService


class TestFieldSuggestionService:
    """Tests pour FieldSuggestionService."""
    
    def test_get_field_suggestions_dialogue(self):
        """Test de suggestions pour le contexte dialogue."""
        service = FieldSuggestionService()
        
        suggestions = service.get_field_suggestions(
            element_type="character",
            context="dialogue",
            available_fields=["Nom", "Dialogue Type", "Caractérisation.Désir", "Autre"]
        )
        
        assert "Nom" in suggestions
        assert "Dialogue Type" in suggestions or any("Dialogue" in s for s in suggestions)
    
    def test_get_field_suggestions_action(self):
        """Test de suggestions pour le contexte action."""
        service = FieldSuggestionService()
        
        suggestions = service.get_field_suggestions(
            element_type="character",
            context="action",
            available_fields=["Nom", "Pouvoirs", "Compétences", "Autre"]
        )
        
        assert "Nom" in suggestions
        assert any("Pouvoir" in s or "Compétence" in s for s in suggestions)
    
    def test_get_field_suggestions_emotional(self):
        """Test de suggestions pour le contexte émotionnel."""
        service = FieldSuggestionService()
        
        suggestions = service.get_field_suggestions(
            element_type="character",
            context="emotional",
            available_fields=["Nom", "Caractérisation.Désir", "Background.Relations"]
        )
        
        assert "Nom" in suggestions
        assert any("Désir" in s or "Relations" in s for s in suggestions)
    
    def test_is_field_suggested(self):
        """Test de vérification si un champ est suggéré."""
        service = FieldSuggestionService()
        
        # Un champ dans "always" devrait être suggéré
        result = service.is_field_suggested("Nom", "character", "dialogue")
        assert result is True
    
    def test_get_suggestion_reason(self):
        """Test de récupération de la raison de suggestion."""
        service = FieldSuggestionService()
        
        reason = service.get_suggestion_reason("Nom", "character", "dialogue")
        assert reason is not None
        assert "essentiel" in reason.lower() or "dialogue" in reason.lower()

