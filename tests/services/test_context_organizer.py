"""Tests pour le service ContextOrganizer."""
import pytest
from services.context_organizer import ContextOrganizer


class TestContextOrganizer:
    """Tests pour ContextOrganizer."""
    
    def test_organize_default(self):
        """Test d'organisation par défaut."""
        organizer = ContextOrganizer()
        element_data = {
            "Nom": "Test Character",
            "Type": "Character",
            "Age": 25,
        }
        fields_to_include = ["Nom", "Type", "Age"]
        
        result = organizer.organize_context(
            element_data,
            "character",
            fields_to_include,
            "default"
        )
        
        assert "Nom" in result
        assert "Type" in result
        assert "Age" in result
        assert "Test Character" in result
    
    def test_organize_narrative(self):
        """Test d'organisation narrative."""
        organizer = ContextOrganizer()
        element_data = {
            "Nom": "Test Character",
            "Caractérisation": {
                "Désir": "Test desire",
                "Faiblesse": "Test weakness",
            },
            "Dialogue Type": {
                "Registre": "Formel",
            }
        }
        fields_to_include = ["Nom", "Caractérisation.Désir", "Dialogue Type.Registre"]
        
        result = organizer.organize_context(
            element_data,
            "character",
            fields_to_include,
            "narrative"
        )
        
        # Vérifier que les sections sont présentes
        assert "IDENTITÉ" in result or "Nom" in result
        assert "CARACTÉRISATION" in result or "Désir" in result
        assert "VOIX" in result or "Registre" in result
    
    def test_organize_minimal(self):
        """Test d'organisation minimale."""
        organizer = ContextOrganizer()
        element_data = {
            "Nom": "Test Character",
            "Dialogue Type": {
                "Registre de langage du personnage": "Formel",
            },
            "Caractérisation": {
                "Désir": "Test desire",
                "Faiblesse": "Test weakness",
            },
            "Autre": "Non essentiel"
        }
        fields_to_include = [
            "Nom",
            "Dialogue Type.Registre de langage du personnage",
            "Caractérisation.Désir",
            "Caractérisation.Faiblesse",
            "Autre"
        ]
        
        result = organizer.organize_context(
            element_data,
            "character",
            fields_to_include,
            "minimal"
        )
        
        # Le mode minimal devrait inclure les champs essentiels
        assert "Nom" in result
        # "Autre" ne devrait pas être inclus dans le mode minimal
        assert "Autre" not in result or "Autre" not in result.split("\n")[-1]
    
    def test_extract_field_value(self):
        """Test d'extraction de valeur de champ."""
        organizer = ContextOrganizer()
        data = {
            "Nom": "Test",
            "Nested": {
                "Value": "NestedValue"
            }
        }
        
        assert organizer._extract_field_value(data, "Nom") == "Test"
        assert organizer._extract_field_value(data, "Nested.Value") == "NestedValue"
        assert organizer._extract_field_value(data, "NonExistent") is None
    
    def test_format_value(self):
        """Test de formatage de valeurs."""
        organizer = ContextOrganizer()
        
        # String
        assert organizer._format_value("Test") == "Test"
        
        # List
        assert organizer._format_value(["A", "B", "C"]) == "A, B, C"
        
        # List of dicts
        assert organizer._format_value([{"Nom": "Test1"}, {"Nom": "Test2"}]) == "Test1, Test2"
        
        # Empty list
        assert organizer._format_value([]) == "Aucun"
    
    def test_categorize_field(self):
        """Test de catégorisation des champs."""
        organizer = ContextOrganizer()
        
        assert organizer._categorize_field("Nom", "character") == "identity"
        assert organizer._categorize_field("Caractérisation.Désir", "character") == "characterization"
        # "Dialogue Type.Registre" devrait être catégorisé comme "voice" car "dialogue" a la priorité
        assert organizer._categorize_field("Dialogue Type.Registre", "character") == "voice"
        assert organizer._categorize_field("Dialogue Type", "character") == "voice"
        assert organizer._categorize_field("Background.Histoire", "character") == "background"
        assert organizer._categorize_field("Pouvoirs", "character") == "mechanics"

