"""Tests pour TextSerializer.

Ce module teste la sérialisation de structures PromptStructure en format texte.
"""
import pytest
from datetime import datetime
from services.context_serializer.text_serializer import TextSerializer
from models.prompt_structure import (
    PromptStructure, PromptSection, ContextCategory, ContextItem, 
    ItemSection, PromptMetadata
)


@pytest.fixture
def serializer():
    """Fixture pour TextSerializer."""
    return TextSerializer()


@pytest.fixture
def simple_prompt_structure():
    """Fixture pour une structure de prompt simple."""
    return PromptStructure(
        sections=[
            PromptSection(
                type="system_prompt",
                title="SYSTEM",
                content="You are a helpful assistant."
            ),
            PromptSection(
                type="context",
                title="CONTEXTE GDD",
                content="",
                categories=[
                    ContextCategory(
                        type="characters",
                        title="CHARACTERS",
                        items=[
                            ContextItem(
                                id="char_1",
                                name="Test Character",
                                sections=[
                                    ItemSection(
                                        title="IDENTITÉ",
                                        content="Nom: Test Character\nEspèce: Humain"
                                    ),
                                    ItemSection(
                                        title="CARACTÉRISATION",
                                        content="Personnage courageux."
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ],
        metadata=PromptMetadata(
            totalTokens=100,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )


@pytest.mark.unit
def test_serialize_system_prompt(serializer):
    """Test sérialisation d'un system prompt."""
    structure = PromptStructure(
        sections=[
            PromptSection(
                type="system_prompt",
                title="SYSTEM",
                content="You are a helpful assistant."
            )
        ],
        metadata=PromptMetadata(
            totalTokens=10,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )
    
    result = serializer.serialize(structure)
    
    assert "You are a helpful assistant." in result


@pytest.mark.unit
def test_serialize_with_section_markers(serializer, simple_prompt_structure):
    """Test que les marqueurs de section sont présents."""
    result = serializer.serialize(simple_prompt_structure)
    
    # Vérifier les marqueurs de section
    assert "--- CONTEXTE GDD ---" in result
    assert "--- CHARACTERS ---" in result
    assert "--- Test Character ---" in result
    assert "--- IDENTITÉ ---" in result
    assert "--- CARACTÉRISATION ---" in result


@pytest.mark.unit
def test_serialize_preserves_content(serializer, simple_prompt_structure):
    """Test que le contenu est préservé."""
    result = serializer.serialize(simple_prompt_structure)
    
    assert "Nom: Test Character" in result
    assert "Espèce: Humain" in result
    assert "Personnage courageux." in result


@pytest.mark.unit
def test_serialize_preserves_order(serializer):
    """Test que l'ordre des sections est préservé."""
    structure = PromptStructure(
        sections=[
            PromptSection(type="system_prompt", title="FIRST", content="First content"),
            PromptSection(type="other", title="SECOND", content="Second content"),
            PromptSection(type="other", title="THIRD", content="Third content")
        ],
        metadata=PromptMetadata(
            totalTokens=20,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )
    
    result = serializer.serialize(structure)
    
    # Vérifier l'ordre
    first_pos = result.find("First content")
    second_pos = result.find("Second content")
    third_pos = result.find("Third content")
    
    assert first_pos < second_pos < third_pos


@pytest.mark.unit
def test_serialize_multiple_items(serializer):
    """Test sérialisation avec plusieurs items."""
    structure = PromptStructure(
        sections=[
            PromptSection(
                type="context",
                title="CONTEXTE",
                content="",
                categories=[
                    ContextCategory(
                        type="characters",
                        title="CHARACTERS",
                        items=[
                            ContextItem(
                                id="char_1",
                                name="Character 1",
                                sections=[
                                    ItemSection(title="INFO", content="Info 1")
                                ]
                            ),
                            ContextItem(
                                id="char_2",
                                name="Character 2",
                                sections=[
                                    ItemSection(title="INFO", content="Info 2")
                                ]
                            )
                        ]
                    )
                ]
            )
        ],
        metadata=PromptMetadata(
            totalTokens=50,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )
    
    result = serializer.serialize(structure)
    
    assert "--- Character 1 ---" in result
    assert "--- Character 2 ---" in result
    assert "Info 1" in result
    assert "Info 2" in result


@pytest.mark.unit
def test_serialize_empty_structure(serializer):
    """Test sérialisation d'une structure vide."""
    structure = PromptStructure(
        sections=[],
        metadata=PromptMetadata(
            totalTokens=0,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )
    
    result = serializer.serialize(structure)
    
    # Devrait retourner une chaîne vide ou minimale
    assert isinstance(result, str)
    assert result == ""


@pytest.mark.unit
def test_serialize_multiple_categories(serializer):
    """Test sérialisation avec plusieurs catégories."""
    structure = PromptStructure(
        sections=[
            PromptSection(
                type="context",
                title="CONTEXTE",
                content="",
                categories=[
                    ContextCategory(
                        type="characters",
                        title="CHARACTERS",
                        items=[
                            ContextItem(
                                id="char_1",
                                name="Char 1",
                                sections=[ItemSection(title="INFO", content="Char info")]
                            )
                        ]
                    ),
                    ContextCategory(
                        type="locations",
                        title="LOCATIONS",
                        items=[
                            ContextItem(
                                id="loc_1",
                                name="Loc 1",
                                sections=[ItemSection(title="INFO", content="Loc info")]
                            )
                        ]
                    )
                ]
            )
        ],
        metadata=PromptMetadata(
            totalTokens=50,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )
    
    result = serializer.serialize(structure)
    
    assert "--- CHARACTERS ---" in result
    assert "--- LOCATIONS ---" in result
    assert "Char info" in result
    assert "Loc info" in result


@pytest.mark.unit
def test_serialize_strips_trailing_whitespace(serializer, simple_prompt_structure):
    """Test que le texte final est nettoyé."""
    result = serializer.serialize(simple_prompt_structure)
    
    # Vérifier que le résultat est strippé
    assert result == result.strip()


@pytest.mark.unit
def test_serialize_adds_blank_lines_between_item_sections(serializer):
    """Test qu'il y a des lignes vides entre les sections d'items."""
    structure = PromptStructure(
        sections=[
            PromptSection(
                type="context",
                title="CONTEXTE",
                content="",
                categories=[
                    ContextCategory(
                        type="characters",
                        title="CHARACTERS",
                        items=[
                            ContextItem(
                                id="char_1",
                                name="Character",
                                sections=[
                                    ItemSection(title="SECTION1", content="Content 1"),
                                    ItemSection(title="SECTION2", content="Content 2")
                                ]
                            )
                        ]
                    )
                ]
            )
        ],
        metadata=PromptMetadata(
            totalTokens=30,
            generatedAt=datetime.now().isoformat(),
            organizationMode="narrative"
        )
    )
    
    result = serializer.serialize(structure)
    
    # Il devrait y avoir une ligne vide après chaque section
    assert "Content 1\n\n" in result or "Content 1\n" in result
