"""Tests pour SectionMapper.

Ce module teste le mapping des sections et champs vers tags XML sémantiques.
"""
import pytest
from services.context_serializer.section_mapper import SectionMapper
from services.context_serializer.field_normalizer import FieldNormalizer


@pytest.fixture
def mapper():
    """Fixture pour SectionMapper."""
    return SectionMapper()


@pytest.mark.unit
def test_get_section_tag_identity(mapper):
    """Test mapping des sections identité."""
    assert mapper.get_section_tag("IDENTITÉ") == ("identity", False)
    assert mapper.get_section_tag("Identité") == ("identity", False)
    assert mapper.get_section_tag("identity") == ("identity", False)


@pytest.mark.unit
def test_get_section_tag_characterization(mapper):
    """Test mapping des sections caractérisation."""
    assert mapper.get_section_tag("CARACTÉRISATION") == ("characterization", False)
    assert mapper.get_section_tag("Caractérisation") == ("characterization", False)
    assert mapper.get_section_tag("characterization") == ("characterization", False)


@pytest.mark.unit
def test_get_section_tag_voice(mapper):
    """Test mapping des sections voix/style."""
    assert mapper.get_section_tag("VOIX") == ("voice", False)
    assert mapper.get_section_tag("Voice") == ("voice", False)
    assert mapper.get_section_tag("STYLE") == ("voice", False)
    assert mapper.get_section_tag("Style") == ("voice", False)


@pytest.mark.unit
def test_get_section_tag_background(mapper):
    """Test mapping des sections histoire/relations."""
    assert mapper.get_section_tag("HISTOIRE") == ("background", False)
    assert mapper.get_section_tag("Histoire") == ("background", False)
    assert mapper.get_section_tag("RELATIONS") == ("background", False)
    assert mapper.get_section_tag("Background") == ("background", False)


@pytest.mark.unit
def test_get_section_tag_mechanics(mapper):
    """Test mapping des sections mécaniques."""
    assert mapper.get_section_tag("MÉCANIQUES") == ("mechanics", False)
    assert mapper.get_section_tag("Mécaniques") == ("mechanics", False)
    assert mapper.get_section_tag("mechanics") == ("mechanics", False)


@pytest.mark.unit
def test_get_section_tag_summary(mapper):
    """Test mapping des sections résumé/introduction."""
    assert mapper.get_section_tag("INTRODUCTION") == ("summary", False)
    assert mapper.get_section_tag("RÉSUMÉ") == ("summary", False)
    assert mapper.get_section_tag("Summary") == ("summary", False)


@pytest.mark.unit
def test_get_section_tag_narrative_arcs(mapper):
    """Test mapping des sections arcs narratifs."""
    assert mapper.get_section_tag("ARCS NARRATIFS") == ("narrative_arcs", False)
    assert mapper.get_section_tag("Arcs Narratifs") == ("narrative_arcs", False)
    assert mapper.get_section_tag("narrative_arcs") == ("narrative_arcs", False)


@pytest.mark.unit
def test_get_section_tag_informations(mapper):
    """Test mapping des sections informations."""
    assert mapper.get_section_tag("INFORMATIONS") == ("informations", True)
    assert mapper.get_section_tag("Informations") == ("informations", True)
    assert mapper.get_section_tag("AUTRES INFORMATIONS") == ("informations", True)


@pytest.mark.unit
def test_get_section_tag_generic(mapper):
    """Test sections génériques non mappées."""
    tag, is_generic = mapper.get_section_tag("Custom Section")
    assert tag == "section"
    assert is_generic is True
    
    tag, is_generic = mapper.get_section_tag("Unknown Title")
    assert tag == "section"
    assert is_generic is True


@pytest.mark.unit
def test_get_section_tag_empty(mapper):
    """Test sections vides."""
    assert mapper.get_section_tag("") == ("informations", True)


@pytest.mark.unit
def test_categorize_field_identity(mapper):
    """Test catégorisation des champs identité."""
    assert mapper.categorize_field("Nom") == ("identity", "name")
    assert mapper.categorize_field("Alias") == ("identity", "alias")
    assert mapper.categorize_field("Espèce") == ("identity", "species")
    assert mapper.categorize_field("Genre") == ("identity", "gender")
    assert mapper.categorize_field("Âge") == ("identity", "age")
    assert mapper.categorize_field("Langage") == ("identity", "language")
    assert mapper.categorize_field("Archétype Littéraire") == ("identity", "archetype")


@pytest.mark.unit
def test_categorize_field_metadata(mapper):
    """Test catégorisation des champs métadonnées."""
    assert mapper.categorize_field("Occupation") == ("metadata", "occupation")
    assert mapper.categorize_field("Sprint") == ("metadata", "sprint")
    assert mapper.categorize_field("État") == ("metadata", "status")
    assert mapper.categorize_field("Communautés") == ("metadata", "communities")
    assert mapper.categorize_field("Type") == ("metadata", "type")


@pytest.mark.unit
def test_categorize_field_relationships(mapper):
    """Test catégorisation des champs relations."""
    assert mapper.categorize_field("Relations Principales") == ("relationships", "main")
    assert mapper.categorize_field("Relations") == ("relationships", "all")


@pytest.mark.unit
def test_categorize_field_unknown(mapper):
    """Test catégorisation des champs inconnus."""
    category, tag = mapper.categorize_field("Custom Field")
    assert category == "metadata"
    assert tag == "custom_field"
    
    category, tag = mapper.categorize_field("Nouveau Champ")
    assert category == "metadata"
    assert tag == "nouveau_champ"


@pytest.mark.unit
def test_categorize_field_with_accents(mapper):
    """Test catégorisation avec accents."""
    category, tag = mapper.categorize_field("Désir Principal")
    assert category == "metadata"
    assert tag == "desir_principal"


@pytest.mark.unit
def test_categorize_field_case_insensitive(mapper):
    """Test que la catégorisation est insensible à la casse."""
    assert mapper.categorize_field("nom") == ("identity", "name")
    assert mapper.categorize_field("NOM") == ("identity", "name")
    assert mapper.categorize_field("Nom") == ("identity", "name")


@pytest.mark.unit
def test_section_mapper_with_custom_normalizer():
    """Test que SectionMapper peut utiliser un FieldNormalizer custom."""
    custom_normalizer = FieldNormalizer()
    mapper = SectionMapper(field_normalizer=custom_normalizer)
    
    category, tag = mapper.categorize_field("Test Field")
    assert category == "metadata"
    assert tag == "test_field"
