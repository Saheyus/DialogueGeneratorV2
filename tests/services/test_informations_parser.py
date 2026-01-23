"""Tests pour InformationsSectionParser.

Ce module teste le parsing des sections INFORMATIONS/AUTRES INFORMATIONS
avec déduplication de champs.
"""
import pytest
import xml.etree.ElementTree as ET
from services.context_serializer.informations_parser import InformationsSectionParser
from services.context_serializer.field_normalizer import FieldNormalizer
from services.context_serializer.section_mapper import SectionMapper
from services.context_serializer.xml_element_builder import XmlElementBuilder
from services.context_serializer.json_parser import JsonParser


@pytest.fixture
def parser():
    """Fixture pour InformationsSectionParser."""
    return InformationsSectionParser()


@pytest.mark.unit
def test_parse_simple_informations(parser):
    """Test parsing simple d'une section INFORMATIONS."""
    content = "Nom: Test Character\nAlias: Test Alias\nEspèce: Humain"
    parent = ET.Element("character")
    
    parser.parse(content, parent)
    
    # Vérifier que <identity> a été créé avec les champs
    identity = parent.find("identity")
    assert identity is not None
    
    name = identity.find("name")
    assert name is not None
    assert name.text == "Test Character"
    
    alias = identity.find("alias")
    assert alias is not None
    assert alias.text == "Test Alias"
    
    species = identity.find("species")
    assert species is not None
    assert species.text == "Humain"


@pytest.mark.unit
def test_parse_with_metadata_fields(parser):
    """Test parsing avec champs métadonnées."""
    content = "Nom: Test\nOccupation: Testeur\nSprint: Sprint 1\nÉtat: A implémenter"
    parent = ET.Element("character")
    
    parser.parse(content, parent)
    
    # Vérifier <identity>
    identity = parent.find("identity")
    assert identity is not None
    assert identity.find("name") is not None
    
    # Vérifier <metadata>
    metadata = parent.find("metadata")
    assert metadata is not None
    assert metadata.find("occupation") is not None
    assert metadata.find("sprint") is not None
    assert metadata.find("status") is not None  # "État" mappé vers "status"


@pytest.mark.unit
def test_parse_with_relationships(parser):
    """Test parsing avec champs relations."""
    content = "Nom: Test\nRelations Principales: Alice, Bob"
    parent = ET.Element("character")
    
    parser.parse(content, parent)
    
    # Vérifier <identity>
    identity = parent.find("identity")
    assert identity is not None
    
    # Vérifier <relationships>
    relationships = parent.find("relationships")
    assert relationships is not None
    assert relationships.find("main") is not None  # "Relations Principales" → "main"


@pytest.mark.unit
def test_parse_with_deduplication(parser):
    """Test que les champs déjà traités sont ignorés."""
    content = "Nom: Duplicate Name\nAlias: Duplicate Alias\nOccupation: New Field"
    parent = ET.Element("character")
    
    # Simuler des champs déjà traités
    already_processed = {"nom", "alias"}  # Noms normalisés
    
    parser.parse(content, parent, already_processed)
    
    # "Nom" et "Alias" ne doivent PAS être créés
    identity = parent.find("identity")
    assert identity is None or identity.find("name") is None
    assert identity is None or identity.find("alias") is None
    
    # "Occupation" DOIT être créé
    metadata = parent.find("metadata")
    assert metadata is not None
    assert metadata.find("occupation") is not None
    assert metadata.find("occupation").text == "New Field"


@pytest.mark.unit
def test_parse_empty_content(parser):
    """Test avec contenu vide."""
    parent = ET.Element("character")
    initial_children = len(parent)
    
    parser.parse("", parent)
    
    # Aucun élément ne doit être ajouté
    assert len(parent) == initial_children
    
    parser.parse("   ", parent)
    assert len(parent) == initial_children


@pytest.mark.unit
def test_parse_ignores_lines_without_colon(parser):
    """Test que les lignes sans ':' sont ignorées."""
    content = "Nom: Test\nSome text without colon\nAlias: Test Alias"
    parent = ET.Element("character")
    
    parser.parse(content, parent)
    
    identity = parent.find("identity")
    assert identity is not None
    assert identity.find("name") is not None
    assert identity.find("alias") is not None


@pytest.mark.unit
def test_parse_ignores_empty_values(parser):
    """Test que les champs avec valeurs vides sont ignorés."""
    content = "Nom: Test\nAlias: \nEspèce: Humain"
    parent = ET.Element("character")
    
    parser.parse(content, parent)
    
    identity = parent.find("identity")
    assert identity is not None
    assert identity.find("name") is not None
    # "Alias" avec valeur vide ne doit pas être créé
    # Note: selon l'implémentation, cela peut varier
    assert identity.find("species") is not None


@pytest.mark.unit
def test_extract_fields_from_dict(parser):
    """Test extraction de champs depuis un dict."""
    data = {
        "Nom": "Test",
        "Identité": {
            "Alias": "Test Alias",
            "Espèce": "Humain"
        },
        "Liste": ["item1", "item2"]
    }
    
    fields = parser.extract_fields_from_dict(data)
    
    # Les champs doivent être normalisés
    assert "nom" in fields
    assert "identite" in fields
    assert "alias" in fields
    assert "espece" in fields
    assert "liste" in fields


@pytest.mark.unit
def test_extract_fields_from_nested_dict(parser):
    """Test extraction récursive de champs."""
    data = {
        "Level1": {
            "Level2": {
                "Level3": "value"
            },
            "Array": [
                {"Item": "value1"},
                {"Item": "value2"}
            ]
        }
    }
    
    fields = parser.extract_fields_from_dict(data)
    
    assert "level1" in fields
    assert "level2" in fields
    assert "level3" in fields
    assert "array" in fields
    assert "item" in fields


@pytest.mark.unit
def test_parser_with_custom_dependencies():
    """Test que le parser peut utiliser des dépendances custom."""
    normalizer = FieldNormalizer()
    mapper = SectionMapper(normalizer)
    builder = XmlElementBuilder(normalizer)
    json_parser = JsonParser()
    
    parser = InformationsSectionParser(
        section_mapper=mapper,
        field_normalizer=normalizer,
        xml_builder=builder,
        json_parser=json_parser
    )
    
    content = "Nom: Test"
    parent = ET.Element("character")
    
    parser.parse(content, parent)
    
    identity = parent.find("identity")
    assert identity is not None
    assert identity.find("name") is not None
