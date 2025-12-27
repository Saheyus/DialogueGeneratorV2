"""Tests pour UnityDialogueGenerationService."""
import pytest
from unittest.mock import MagicMock, AsyncMock

from services.unity_dialogue_generation_service import UnityDialogueGenerationService
from models.dialogue_structure.unity_dialogue_node import (
    UnityDialogueGenerationResponse,
    UnityDialogueNodeContent,
    UnityDialogueChoiceContent
)


@pytest.fixture
def unity_service() -> UnityDialogueGenerationService:
    """Fixture pour créer un UnityDialogueGenerationService."""
    return UnityDialogueGenerationService()


@pytest.fixture
def mock_llm_client():
    """Fixture pour créer un mock LLM client."""
    client = MagicMock()
    return client


@pytest.mark.asyncio
async def test_generate_dialogue_node_single_node(unity_service: UnityDialogueGenerationService, mock_llm_client):
    """Test que generate_dialogue_node génère un seul nœud."""
    # Créer un mock de réponse avec un seul nœud
    mock_response = UnityDialogueGenerationResponse(
        title="Test Dialogue",
        node=UnityDialogueNodeContent(
            speaker="TEST_NPC",
            line="Test dialogue line",
            choices=[
                UnityDialogueChoiceContent(
                    text="Choice 1",
                    targetNode=None
                ),
                UnityDialogueChoiceContent(
                    text="Choice 2",
                    targetNode=None
                )
            ]
        )
    )
    
    mock_llm_client.generate_variants = AsyncMock(return_value=[mock_response])
    
    result = await unity_service.generate_dialogue_node(
        llm_client=mock_llm_client,
        prompt="Test prompt",
        max_choices=2
    )
    
    assert isinstance(result, UnityDialogueGenerationResponse)
    assert result.title == "Test Dialogue"
    assert result.node.speaker == "TEST_NPC"
    assert result.node.line == "Test dialogue line"
    assert result.node.choices is not None
    assert len(result.node.choices) == 2


@pytest.mark.asyncio
async def test_enrich_with_ids_single_node(unity_service: UnityDialogueGenerationService):
    """Test que enrich_with_ids fonctionne avec un seul nœud."""
    response = UnityDialogueGenerationResponse(
        title="Test Dialogue",
        node=UnityDialogueNodeContent(
            speaker="TEST_NPC",
            line="Test dialogue line",
            choices=[
                UnityDialogueChoiceContent(
                    text="Choice 1",
                    targetNode=None
                )
            ]
        )
    )
    
    enriched_nodes = unity_service.enrich_with_ids(response, start_id="START")
    
    assert len(enriched_nodes) == 1
    node = enriched_nodes[0]
    assert node["id"] == "START"
    assert node["speaker"] == "TEST_NPC"
    assert node["line"] == "Test dialogue line"
    assert "choices" in node
    assert len(node["choices"]) == 1
    assert node["choices"][0]["text"] == "Choice 1"
    assert node["choices"][0]["targetNode"] == ""  # Vide mais présent


def test_enrich_with_ids_no_choices(unity_service: UnityDialogueGenerationService):
    """Test enrich_with_ids avec un nœud sans choix."""
    response = UnityDialogueGenerationResponse(
        title="Test Dialogue",
        node=UnityDialogueNodeContent(
            speaker="TEST_NPC",
            line="Test dialogue line",
            nextNode="END"
        )
    )
    
    enriched_nodes = unity_service.enrich_with_ids(response, start_id="START")
    
    assert len(enriched_nodes) == 1
    node = enriched_nodes[0]
    assert node["id"] == "START"
    assert node["speaker"] == "TEST_NPC"
    assert node["line"] == "Test dialogue line"
    assert "nextNode" in node
    assert node["nextNode"] == "END"
    assert "choices" not in node

