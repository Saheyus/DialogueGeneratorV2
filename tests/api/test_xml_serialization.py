"""Tests pour la sérialisation XML du prompt.

Ce module teste la conversion du contexte JSON en XML pour le LLM.
"""
import pytest
import xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
from api.main import app
from context_builder import ContextBuilder
from models.prompt_structure import PromptStructure, PromptSection, ContextCategory, ContextItem, ItemSection, PromptMetadata
from datetime import datetime


@pytest.fixture
def context_builder():
    """Fixture pour ContextBuilder."""
    return ContextBuilder()


@pytest.fixture
def sample_prompt_structure():
    """Fixture pour une structure de prompt de test."""
    return PromptStructure(
        sections=[
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
                                id="PNJ_1",
                                name="PNJ 1",
                                sections=[
                                    ItemSection(
                                        title="IDENTITÉ",
                                        content="Nom: Test Character\nEspèce: Humain"
                                    ),
                                    ItemSection(
                                        title="CARACTÉRISATION",
                                        content="Personnage courageux et déterminé."
                                    )
                                ],
                                metadata={"name": "Test Character"}
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
def test_serialize_context_to_xml_generates_valid_xml(context_builder, sample_prompt_structure):
    """Test que serialize_context_to_xml() retourne un ET.Element valide."""
    xml_element = context_builder._context_serializer.serialize_to_xml(sample_prompt_structure)
    
    # Vérifier que c'est un ET.Element
    assert isinstance(xml_element, ET.Element)
    
    # Vérifier la structure de base
    assert xml_element.tag == "context"
    assert len(xml_element) > 0  # Doit avoir au moins une catégorie


@pytest.mark.unit
def test_serialize_context_to_xml_structure(context_builder, sample_prompt_structure):
    """Test que la structure XML est correcte."""
    root = context_builder._context_serializer.serialize_to_xml(sample_prompt_structure)
    
    # Vérifier que c'est un ET.Element
    assert isinstance(root, ET.Element)
    
    # Vérifier la hiérarchie : context > characters > character > sections
    assert root.tag == "context"
    
    characters_elem = root.find("characters")
    assert characters_elem is not None, "Élément <characters> manquant"
    
    character_elem = characters_elem.find("character")
    assert character_elem is not None, "Élément <character> manquant"
    
    # Vérifier les sections
    identity_elem = character_elem.find("identity")
    assert identity_elem is not None, "Élément <identity> manquant"
    assert identity_elem.text is not None
    assert "Test Character" in identity_elem.text or "Humain" in identity_elem.text


@pytest.mark.unit
def test_serialize_context_to_xml_escapes_special_characters(context_builder):
    """Test que les caractères spéciaux XML sont correctement échappés."""
    # Créer une structure avec des caractères spéciaux
    structure = PromptStructure(
        sections=[
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
                                id="PNJ_1",
                                name="PNJ 1",
                                sections=[
                                    ItemSection(
                                        title="IDENTITÉ",
                                        content="Nom: Test & Character <with> special chars"
                                    )
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
    
    root = context_builder._context_serializer.serialize_to_xml(structure)
    
    # Vérifier que c'est un ET.Element
    assert isinstance(root, ET.Element)
    
    # Vérifier que les caractères sont échappés dans le texte
    # On convertit en string pour vérifier l'échappement
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    assert "&amp;" in xml_str or "&lt;" in xml_str or "&gt;" in xml_str


@pytest.mark.integration
@pytest.mark.api
def test_prompt_xml_format(real_client):
    """Test que le prompt retourné par l'API est en format XML."""
    from context_builder import ContextBuilder
    cb = ContextBuilder()
    cb.load_gdd_files()
    all_characters = cb.get_characters_names()
    test_character = all_characters[0] if all_characters else "Test Character"
    
    response = real_client.post(
        "/api/v1/dialogues/estimate-tokens",
        json={
            "context_selections": {
                "characters_full": [test_character],
                "locations_full": [],
                "items_full": [],
                "species_full": [],
                "communities_full": []
            },
            "user_instructions": "Test XML format",
            "max_context_tokens": 1000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    raw_prompt = data.get("raw_prompt", "")
    
    # Vérifier que c'est du XML
    assert raw_prompt.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    
    # Parser le XML pour vérifier qu'il est bien formé
    xml_content = raw_prompt.split('?>', 1)[-1].strip()
    root = ET.fromstring(xml_content)
    
    # Vérifier la structure de base
    assert root.tag == "prompt"
    
    # Vérifier la présence des sections principales
    assert root.find("contract") is not None or root.find("technical") is not None or root.find("context") is not None


@pytest.mark.integration
@pytest.mark.api
def test_debug_raw_json_endpoint(real_client):
    """Test que l'endpoint debug/raw-json retourne le JSON brut."""
    from context_builder import ContextBuilder
    cb = ContextBuilder()
    cb.load_gdd_files()
    all_characters = cb.get_characters_names()
    test_character = all_characters[0] if all_characters else "Test Character"
    
    response = real_client.post(
        "/api/v1/dialogues/debug/raw-json",
        json={
            "context_selections": {
                "characters_full": [test_character],
                "locations_full": [],
                "items_full": [],
                "species_full": [],
                "communities_full": []
            },
            "user_instructions": "Test debug endpoint",
            "max_context_tokens": 1000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier la structure de la réponse
    assert "structured_context" in data
    assert "prompt_hash" in data
    
    # Vérifier que structured_context est un dict (JSON)
    structured_context = data["structured_context"]
    assert isinstance(structured_context, dict)
    
    # Vérifier la structure de base du JSON
    assert "sections" in structured_context
    assert "metadata" in structured_context


@pytest.mark.integration
@pytest.mark.api
def test_structured_prompt_remains_json(real_client):
    """Test que structured_prompt reste en JSON pour l'UI."""
    from context_builder import ContextBuilder
    cb = ContextBuilder()
    cb.load_gdd_files()
    all_characters = cb.get_characters_names()
    test_character = all_characters[0] if all_characters else "Test Character"
    
    response = real_client.post(
        "/api/v1/dialogues/estimate-tokens",
        json={
            "context_selections": {
                "characters_full": [test_character],
                "locations_full": [],
                "items_full": [],
                "species_full": [],
                "communities_full": []
            },
            "user_instructions": "Test structured prompt",
            "max_context_tokens": 1000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier que raw_prompt est en XML
    raw_prompt = data.get("raw_prompt", "")
    assert raw_prompt.startswith('<?xml')
    
    # Vérifier que structured_prompt est en JSON (dict)
    structured_prompt = data.get("structured_prompt")
    if structured_prompt:
        assert isinstance(structured_prompt, dict)
        assert "sections" in structured_prompt
        assert "metadata" in structured_prompt


@pytest.mark.unit
def test_no_generic_section_tags(context_builder):
    """Test que les tags génériques <section> ne sont plus utilisés."""
    structure = PromptStructure(
        sections=[
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
                                id="PNJ_1",
                                name="PNJ 1",
                                sections=[
                                    ItemSection(
                                        title="INFORMATIONS",
                                        content="Nom: Test Character\nAlias: Test Alias\nEspèce: Humain"
                                    ),
                                    ItemSection(
                                        title="CARACTÉRISATION",
                                        content='{"Faiblesse": "Test weakness", "Compulsion": "Test compulsion"}'
                                    )
                                ],
                                metadata={"name": "Test Character"}
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
    
    root = context_builder._context_serializer.serialize_to_xml(structure)
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    
    # Vérifier qu'il n'y a pas de tags <section>
    assert "<section" not in xml_str, "Tags génériques <section> ne doivent plus être utilisés"
    
    # Vérifier que INFORMATIONS est déstructuré en <identity> et <metadata>
    character_elem = root.find(".//character")
    assert character_elem is not None
    identity_elem = character_elem.find("identity")
    assert identity_elem is not None, "Section INFORMATIONS doit être déstructurée en <identity>"
    
    # Vérifier que le JSON est déstructuré
    characterization_elem = character_elem.find("characterization")
    assert characterization_elem is not None
    # Vérifier qu'il n'y a pas de JSON brut dans le texte
    if characterization_elem.text:
        assert not (characterization_elem.text.strip().startswith("{") or 
                   characterization_elem.text.strip().startswith("[")), \
            "JSON ne doit pas être présent en texte brut, doit être déstructuré"
    
    # Vérifier la structure déstructurée du JSON
    weakness_elem = characterization_elem.find("weakness")
    compulsion_elem = characterization_elem.find("compulsion")
    assert weakness_elem is not None or compulsion_elem is not None, \
        "JSON doit être déstructuré en éléments XML"


@pytest.mark.unit
def test_informations_section_parsed(context_builder):
    """Test que la section INFORMATIONS est correctement parsée en structure XML."""
    structure = PromptStructure(
        sections=[
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
                                id="PNJ_1",
                                name="PNJ 1",
                                sections=[
                                    ItemSection(
                                        title="INFORMATIONS",
                                        content="Nom: Test Character\nAlias: Test Alias\nEspèce: Humain\nOccupation: Testeur"
                                    )
                                ],
                                metadata={"name": "Test Character"}
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
    
    root = context_builder._context_serializer.serialize_to_xml(structure)
    character_elem = root.find(".//character")
    assert character_elem is not None
    
    # Vérifier que <identity> existe avec les champs appropriés
    identity_elem = character_elem.find("identity")
    assert identity_elem is not None, "Section INFORMATIONS doit créer <identity>"
    
    name_elem = identity_elem.find("name")
    alias_elem = identity_elem.find("alias")
    species_elem = identity_elem.find("species")
    
    assert name_elem is not None, "Champ 'Nom' doit être dans <identity><name>"
    assert name_elem.text == "Test Character"
    assert alias_elem is not None, "Champ 'Alias' doit être dans <identity><alias>"
    assert species_elem is not None, "Champ 'Espèce' doit être dans <identity><species>"
    
    # Vérifier que <metadata> existe avec les champs appropriés
    metadata_elem = character_elem.find("metadata")
    assert metadata_elem is not None, "Champs métadonnées doivent être dans <metadata>"
    
    occupation_elem = metadata_elem.find("occupation")
    assert occupation_elem is not None, "Champ 'Occupation' doit être dans <metadata><occupation>"
    assert occupation_elem.text == "Testeur"


@pytest.mark.unit
def test_json_content_destructured(context_builder):
    """Test que le contenu JSON est déstructuré en éléments XML."""
    structure = PromptStructure(
        sections=[
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
                                id="PNJ_1",
                                name="PNJ 1",
                                sections=[
                                    ItemSection(
                                        title="CARACTÉRISATION",
                                        content='{"Faiblesse": "Test weakness", "Compulsion": "Test compulsion", "Désir": "Test desire"}'
                                    )
                                ],
                                metadata={"name": "Test Character"}
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
    
    root = context_builder._context_serializer.serialize_to_xml(structure)
    characterization_elem = root.find(".//characterization")
    assert characterization_elem is not None
    
    # Vérifier que le JSON est déstructuré en éléments XML
    weakness_elem = characterization_elem.find("weakness")
    compulsion_elem = characterization_elem.find("compulsion")
    desire_elem = characterization_elem.find("desire")
    
    assert weakness_elem is not None, "JSON doit être déstructuré en <weakness>"
    assert weakness_elem.text == "Test weakness"
    assert compulsion_elem is not None, "JSON doit être déstructuré en <compulsion>"
    assert compulsion_elem.text == "Test compulsion"
    assert desire_elem is not None, "JSON doit être déstructuré en <desire>"
    assert desire_elem.text == "Test desire"
    
    # Vérifier qu'il n'y a pas de JSON brut dans le texte
    if characterization_elem.text:
        assert not characterization_elem.text.strip().startswith("{"), \
            "Ne doit pas y avoir de JSON brut dans le texte"


@pytest.fixture
def real_client():
    """Client de test sans mocks - utilise les vrais services."""
    yield TestClient(app)
