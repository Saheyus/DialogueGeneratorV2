"""Tests pour FieldNormalizer.

Ce module teste la normalisation des noms de champs pour comparaison et
génération de tags XML valides.
"""
import pytest
from services.context_serializer.field_normalizer import FieldNormalizer


@pytest.fixture
def normalizer():
    """Fixture pour FieldNormalizer."""
    return FieldNormalizer()


@pytest.mark.unit
def test_normalize_for_comparison_basic(normalizer):
    """Test normalisation basique pour comparaison."""
    assert normalizer.normalize_for_comparison("Nom") == "nom"
    assert normalizer.normalize_for_comparison("Alias") == "alias"
    assert normalizer.normalize_for_comparison("OCCUPATION") == "occupation"


@pytest.mark.unit
def test_normalize_for_comparison_with_accents(normalizer):
    """Test normalisation avec accents."""
    assert normalizer.normalize_for_comparison("Identité") == "identite"
    assert normalizer.normalize_for_comparison("Désir Principal") == "desir_principal"
    assert normalizer.normalize_for_comparison("Espèce") == "espece"
    assert normalizer.normalize_for_comparison("Âge") == "age"


@pytest.mark.unit
def test_normalize_for_comparison_with_spaces(normalizer):
    """Test normalisation avec espaces."""
    assert normalizer.normalize_for_comparison("Désir Principal") == "desir_principal"
    assert normalizer.normalize_for_comparison("Relations Principales") == "relations_principales"
    assert normalizer.normalize_for_comparison("Axe Idéologique") == "axe_ideologique"


@pytest.mark.unit
def test_normalize_for_comparison_with_special_chars(normalizer):
    """Test normalisation avec caractères spéciaux."""
    assert normalizer.normalize_for_comparison("Type (jeu)") == "type_jeu"
    assert normalizer.normalize_for_comparison("Nom/Alias") == "nom_alias"
    assert normalizer.normalize_for_comparison("Lieux-de-vie") == "lieux_de_vie"


@pytest.mark.unit
def test_normalize_for_comparison_empty(normalizer):
    """Test normalisation avec chaînes vides."""
    assert normalizer.normalize_for_comparison("") == ""
    assert normalizer.normalize_for_comparison("   ") == ""


@pytest.mark.unit
def test_normalize_for_comparison_multiple_underscores(normalizer):
    """Test que les underscores multiples sont réduits."""
    assert normalizer.normalize_for_comparison("Nom___Alias") == "nom_alias"
    assert normalizer.normalize_for_comparison("Test  Multiple  Spaces") == "test_multiple_spaces"


@pytest.mark.unit
def test_normalize_for_xml_tag_basic(normalizer):
    """Test normalisation basique pour tags XML."""
    assert normalizer.normalize_for_xml_tag("Nom") == "nom"
    assert normalizer.normalize_for_xml_tag("Alias") == "alias"


@pytest.mark.unit
def test_normalize_for_xml_tag_with_accents(normalizer):
    """Test normalisation XML avec accents."""
    assert normalizer.normalize_for_xml_tag("Identité") == "identite"
    assert normalizer.normalize_for_xml_tag("Désir Principal") == "desir_principal"
    assert normalizer.normalize_for_xml_tag("Espèce") == "espece"


@pytest.mark.unit
def test_normalize_for_xml_tag_starts_with_digit(normalizer):
    """Test que les tags commençant par un chiffre sont préfixés."""
    assert normalizer.normalize_for_xml_tag("2ème Nom") == "field_2eme_nom"
    assert normalizer.normalize_for_xml_tag("1er Objectif") == "field_1er_objectif"


@pytest.mark.unit
def test_normalize_for_xml_tag_empty(normalizer):
    """Test normalisation XML avec chaînes vides."""
    assert normalizer.normalize_for_xml_tag("") == "field"
    assert normalizer.normalize_for_xml_tag("   ") == "field"


@pytest.mark.unit
def test_normalize_for_xml_tag_special_chars(normalizer):
    """Test normalisation XML avec caractères spéciaux."""
    assert normalizer.normalize_for_xml_tag("Type (jeu)") == "type_jeu"
    assert normalizer.normalize_for_xml_tag("Nom/Alias") == "nom_alias"
    assert normalizer.normalize_for_xml_tag("Lieux-de-vie") == "lieux_de_vie"


@pytest.mark.unit
def test_normalize_for_xml_tag_no_double_underscores(normalizer):
    """Test que les underscores multiples sont réduits."""
    assert normalizer.normalize_for_xml_tag("Nom___Alias") == "nom_alias"
    assert normalizer.normalize_for_xml_tag("Test  Multiple  Spaces") == "test_multiple_spaces"


@pytest.mark.unit
def test_normalize_for_comparison_idempotent(normalizer):
    """Test que la normalisation est idempotente."""
    result1 = normalizer.normalize_for_comparison("Désir Principal")
    result2 = normalizer.normalize_for_comparison(result1)
    # Note: result1 est déjà normalisé, donc result2 devrait être identique
    assert result1 == "desir_principal"
    # Pas forcément idempotent car lowercase n'a pas d'effet sur du déjà lowercase
    assert result2 == "desir_principal"


@pytest.mark.unit
def test_normalize_for_xml_tag_common_french_accents(normalizer):
    """Test normalisation de tous les accents français communs."""
    assert normalizer.normalize_for_xml_tag("Référence") == "reference"
    assert normalizer.normalize_for_xml_tag("Événement") == "evenement"
    assert normalizer.normalize_for_xml_tag("Côté") == "cote"
    assert normalizer.normalize_for_xml_tag("Naïveté") == "naivete"
    assert normalizer.normalize_for_xml_tag("Façade") == "facade"
