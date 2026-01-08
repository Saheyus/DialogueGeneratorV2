"""Tests pour le service ContextFormatter."""
import pytest
from pathlib import Path
from services.context_formatter import ContextFormatter


@pytest.fixture
def sample_config():
    """Configuration de test."""
    return {
        "character": {
            "1": [
                {"path": "Nom", "label": "Nom", "truncate": -1},
                {"path": "Age", "label": "Âge", "truncate": -1},
                {"path": "Introduction.Résumé", "label": "Résumé", "truncate": 200}
            ],
            "2": [
                {"path": "Background.Histoire", "label": "Histoire", "truncate": 500}
            ]
        }
    }


@pytest.fixture
def formatter(sample_config):
    """Formatter de test."""
    return ContextFormatter(sample_config)


@pytest.fixture
def sample_element_data():
    """Données d'élément de test."""
    return {
        "Nom": "Test Character",
        "Age": 25,
        "Introduction": {
            "Résumé": "Un personnage de test avec un résumé"
        },
        "Background": {
            "Histoire": "Une histoire très longue qui devrait être tronquée si nécessaire"
        }
    }


class TestContextFormatter:
    """Tests pour ContextFormatter."""
    
    def test_init(self, sample_config):
        """Test d'initialisation."""
        formatter = ContextFormatter(sample_config)
        
        assert formatter.config == sample_config
    
    def test_load_config(self, tmp_path):
        """Test de chargement de configuration depuis fichier."""
        config_file = tmp_path / "test_config.json"
        config_data = {"character": {"1": [{"path": "Nom", "label": "Nom"}]}}
        
        import json
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        
        result = ContextFormatter.load_config(config_file)
        
        assert result == config_data
    
    def test_load_config_not_found(self, tmp_path):
        """Test de chargement avec fichier inexistant."""
        config_file = tmp_path / "nonexistent.json"
        result = ContextFormatter.load_config(config_file)
        
        assert result == {}
    
    def test_extract_from_dict_simple(self):
        """Test d'extraction simple depuis un dict."""
        data = {"Nom": "Test", "Age": 25}
        result = ContextFormatter._extract_from_dict(data, "Nom")
        
        assert result == "Test"
    
    def test_extract_from_dict_nested(self):
        """Test d'extraction avec chemin pointé."""
        data = {"Introduction": {"Résumé": "Test summary"}}
        result = ContextFormatter._extract_from_dict(data, "Introduction.Résumé")
        
        assert result == "Test summary"
    
    def test_extract_from_dict_not_found(self):
        """Test d'extraction avec chemin inexistant."""
        data = {"Nom": "Test"}
        result = ContextFormatter._extract_from_dict(data, "Nonexistent", default="N/A")
        
        assert result == "N/A"
    
    def test_format_list(self):
        """Test de formatage de liste."""
        data_list = ["Item 1", "Item 2", "Item 3"]
        result = ContextFormatter._format_list(data_list)
        
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
    
    def test_format_list_empty(self):
        """Test de formatage de liste vide."""
        result = ContextFormatter._format_list([])
        
        assert result == "N/A"
    
    def test_format_element_level_1(self, formatter, sample_element_data):
        """Test de formatage d'élément niveau 1."""
        result = formatter.format_element(sample_element_data, "character", 1)
        
        assert "Nom" in result
        assert "Test Character" in result
        assert "Âge" in result
        assert "25" in result
    
    def test_format_element_level_2(self, formatter, sample_element_data):
        """Test de formatage d'élément niveau 2."""
        result = formatter.format_element(sample_element_data, "character", 2)
        
        # Doit inclure les champs de niveau 1 et 2
        assert "Nom" in result
        assert "Histoire" in result
    
    def test_format_element_no_config(self, sample_element_data):
        """Test de formatage sans configuration (fallback)."""
        formatter = ContextFormatter({})
        result = formatter.format_element(sample_element_data, "character", 1)
        
        # Doit formater toutes les clés disponibles
        assert "Nom" in result
        assert "Age" in result
    
    def test_apply_excerpt_truncation(self, formatter):
        """Test de troncature pour mode excerpt."""
        long_text = "A" * 500
        config_with_truncate = {
            "character": {
                "1": [
                    {"path": "text", "label": "Texte (extrait)", "truncate": 100}
                ]
            }
        }
        formatter_with_truncate = ContextFormatter(config_with_truncate)
        
        result = formatter_with_truncate._apply_excerpt_truncation(long_text, "character")
        
        # Le texte devrait être tronqué
        assert len(result) < len(long_text)
        assert "... (extrait)" in result
    
    def test_apply_excerpt_truncation_no_truncate(self, formatter):
        """Test de troncature sans paramètre de troncature."""
        text = "Short text"
        result = formatter._apply_excerpt_truncation(text, "character")
        
        # Le texte ne devrait pas être modifié
        assert result == text
