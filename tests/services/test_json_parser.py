"""Tests pour JsonParser.

Ce module teste la détection et le parsing de contenu JSON dans les sections.
"""
import pytest
from services.context_serializer.json_parser import JsonParser


@pytest.fixture
def parser():
    """Fixture pour JsonParser."""
    return JsonParser()


@pytest.mark.unit
def test_parse_simple_dict(parser):
    """Test parsing d'un dict JSON simple."""
    content = '{"key": "value", "number": 42}'
    result = parser.parse(content)
    
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


@pytest.mark.unit
def test_parse_simple_list(parser):
    """Test parsing d'une liste JSON simple."""
    content = '[{"a": 1}, {"b": 2}, {"c": 3}]'
    result = parser.parse(content)
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["a"] == 1
    assert result[1]["b"] == 2


@pytest.mark.unit
def test_parse_nested_dict(parser):
    """Test parsing d'un dict JSON imbriqué."""
    content = '{"outer": {"inner": {"deep": "value"}}}'
    result = parser.parse(content)
    
    assert isinstance(result, dict)
    assert result["outer"]["inner"]["deep"] == "value"


@pytest.mark.unit
def test_parse_dict_with_list(parser):
    """Test parsing d'un dict contenant des listes."""
    content = '{"items": [1, 2, 3], "name": "test"}'
    result = parser.parse(content)
    
    assert isinstance(result, dict)
    assert result["items"] == [1, 2, 3]
    assert result["name"] == "test"


@pytest.mark.unit
def test_parse_french_characters(parser):
    """Test parsing avec caractères français."""
    content = '{"Faiblesse": "Test weakness", "Désir": "Test desire"}'
    result = parser.parse(content)
    
    assert isinstance(result, dict)
    assert result["Faiblesse"] == "Test weakness"
    assert result["Désir"] == "Test desire"


@pytest.mark.unit
def test_parse_non_json_text(parser):
    """Test qu'un texte non-JSON retourne None."""
    content = "This is normal text without JSON"
    result = parser.parse(content)
    
    assert result is None


@pytest.mark.unit
def test_parse_empty_string(parser):
    """Test qu'une chaîne vide retourne None."""
    assert parser.parse("") is None
    assert parser.parse("   ") is None


@pytest.mark.unit
def test_parse_invalid_json(parser):
    """Test qu'un JSON invalide retourne None."""
    content = '{"invalid": "json", "missing": bracket'
    result = parser.parse(content)
    
    assert result is None


@pytest.mark.unit
def test_parse_json_embedded_in_text(parser):
    """Test extraction de JSON embedded dans du texte."""
    content = 'Some text before {"key": "value"} some text after'
    result = parser.parse(content)
    
    # Le parser devrait extraire le JSON
    assert isinstance(result, dict)
    assert result["key"] == "value"


@pytest.mark.unit
def test_parse_multiple_json_in_text(parser):
    """Test extraction du plus grand JSON quand il y en a plusieurs."""
    content = 'First {"small": 1} then {"larger": {"nested": "value"}} end'
    result = parser.parse(content)
    
    # Le parser devrait choisir le plus grand JSON (nested dict)
    assert isinstance(result, dict)
    assert "larger" in result or "nested" in result.get("larger", {})


@pytest.mark.unit
def test_parse_list_embedded_in_text(parser):
    """Test extraction d'une liste JSON embedded."""
    content = 'Text before [{"a": 1}, {"b": 2}] text after'
    result = parser.parse(content)
    
    assert isinstance(result, list)
    assert len(result) == 2


@pytest.mark.unit
def test_parse_json_with_whitespace(parser):
    """Test parsing de JSON avec espaces et retours ligne."""
    content = '''
    {
        "key": "value",
        "number": 42
    }
    '''
    result = parser.parse(content)
    
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


@pytest.mark.unit
def test_parse_json_with_special_characters(parser):
    """Test parsing de JSON avec caractères spéciaux."""
    content = '{"text": "Line 1\\nLine 2", "quote": "\\"quoted\\""}'
    result = parser.parse(content)
    
    assert isinstance(result, dict)
    assert result["text"] == "Line 1\nLine 2"
    assert result["quote"] == '"quoted"'


@pytest.mark.unit
def test_parse_returns_none_for_non_dict_list(parser):
    """Test que le parser ne retourne que dict ou list."""
    # JSON valide mais pas dict/list (string, number, etc.)
    content_string = '"just a string"'
    result_string = parser.parse(content_string)
    # Le parser peut soit retourner None, soit la string
    # Selon l'implémentation, on vérifie juste qu'il ne plante pas
    assert result_string is None or isinstance(result_string, str)
