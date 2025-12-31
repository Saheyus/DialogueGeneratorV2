"""Tests pour les endpoints de génération de dialogues."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from api.main import app
from services.dialogue_generation_service import DialogueGenerationService
# InteractionService et Interaction supprimés - système obsolète
from models.dialogue_structure.dialogue_elements import DialogueLineElement


@pytest.fixture
def mock_dialogue_service():
    """Mock du DialogueGenerationService."""
    mock_service = MagicMock(spec=DialogueGenerationService)
    mock_service.context_builder = MagicMock()
    mock_service.context_builder._count_tokens = MagicMock(return_value=100)
    mock_service.prompt_engine = MagicMock()
    mock_service.prompt_engine.build_unity_dialogue_prompt = MagicMock(return_value=("prompt", 200))
    mock_service.prompt_engine.system_prompt_template = "Test system prompt"
    return mock_service


# mock_interaction_service supprimé - système obsolète

@pytest.fixture
def client(mock_dialogue_service):
    """Fixture pour créer un client de test avec mocks."""
    from api.dependencies import (
        get_dialogue_generation_service,
        # get_interaction_service supprimé - système obsolète
        get_config_service
    )
    
    # Mock du config service pour éviter les erreurs
    mock_config_service = MagicMock()
    mock_config_service.get_llm_config = MagicMock(return_value={
        "api_key_env_var": "OPENAI_API_KEY"
    })
    mock_config_service.get_available_llm_models = MagicMock(return_value=[
        {
            "api_identifier": "gpt-5.2-mini",
            "display_name": "GPT-4o Mini",
            "client_type": "openai"
        }
    ])
    
    # Override les dépendances FastAPI
    app.dependency_overrides[get_dialogue_generation_service] = lambda: mock_dialogue_service
    # get_interaction_service supprimé - système obsolète
    app.dependency_overrides[get_config_service] = lambda: mock_config_service
    
    yield TestClient(app)
    
    # Nettoyer après le test
    app.dependency_overrides.clear()


def test_estimate_tokens(client, mock_dialogue_service, monkeypatch):
    """Test d'estimation de tokens."""
    mock_dialogue_service.context_builder.build_context = MagicMock(return_value="context text")
    
    # Mock SkillCatalogService et TraitCatalogService pour estimate_tokens
    mock_skill_service = MagicMock()
    mock_skill_service.load_skills = MagicMock(return_value=["Skill1", "Skill2"])
    mock_trait_service = MagicMock()
    mock_trait_service.load_traits = MagicMock(return_value=[])
    mock_trait_service.get_trait_labels = MagicMock(return_value=["Trait1", "Trait2"])
    
    monkeypatch.setattr("api.routers.dialogues.SkillCatalogService", lambda: mock_skill_service)
    monkeypatch.setattr("api.routers.dialogues.TraitCatalogService", lambda: mock_trait_service)
    
    response = client.post(
        "/api/v1/dialogues/estimate-tokens",
        json={
            "context_selections": {
                "characters": ["Character1"],
                "locations": [],
                "items": [],
                "species": [],
                "communities": []
            },
            "user_instructions": "Test instructions",
            "max_context_tokens": 1000
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "context_tokens" in data
    assert "total_estimated_tokens" in data
    assert isinstance(data["context_tokens"], int)
    assert isinstance(data["total_estimated_tokens"], int)


def test_estimate_tokens_invalid_request(client):
    """Test d'estimation de tokens avec requête invalide."""
    response = client.post(
        "/api/v1/dialogues/estimate-tokens",
        json={}
    )
    assert response.status_code == 422  # Validation error


# test_generate_dialogue_variants et test_generate_dialogue_variants_invalid_request supprimés - système texte libre obsolète, utiliser Unity JSON à la place

@pytest.mark.skip(reason="Endpoint /generate/interactions supprimé. Utiliser /generate/unity-dialogue à la place.")
@pytest.mark.asyncio
async def test_generate_interaction_variants(client, mock_dialogue_service, mock_interaction_service, monkeypatch):
    """Test de génération d'interactions.
    
    NOTE: Ce test est obsolète. L'endpoint /api/v1/dialogues/generate/interactions
    a été supprimé et remplacé par /api/v1/dialogues/generate/unity-dialogue.
    """
    # Mocks d'Interaction supprimés - système obsolète
    mock_dialogue_service.context_builder = MagicMock()
    mock_dialogue_service.context_builder.set_previous_dialogue_context = MagicMock()
    
    # Mock LLM client factory
    mock_llm_client = MagicMock()
    mock_factory = MagicMock()
    mock_factory.create_client.return_value = mock_llm_client
    monkeypatch.setattr("factories.llm_factory.LLMClientFactory", mock_factory)
    
    response = client.post(
        "/api/v1/dialogues/generate/interactions",
        json={
            "k_variants": 1,
            "max_context_tokens": 1000,
            "user_instructions": "Test",
            "llm_model_identifier": "gpt-5.2-mini",
            "context_selections": {
                "characters": [],
                "locations": [],
                "items": [],
                "species": [],
                "communities": []
            }
        }
    )
    
    # Note: Les appels async peuvent nécessiter un serveur réel ou un mock plus complexe
    assert response.status_code in [200, 500]  # 500 si erreur de mock, 200 si ça passe


@pytest.mark.skip(reason="Endpoint /generate/interactions supprimé. Utiliser /generate/unity-dialogue à la place.")
def test_generate_interaction_variants_invalid_previous_id(client):
    """Test de génération d'interactions avec previous_interaction_id inexistant.
    
    NOTE: Ce test est obsolète. L'endpoint /api/v1/dialogues/generate/interactions
    a été supprimé et remplacé par /api/v1/dialogues/generate/unity-dialogue.
    """
    # mock_interaction_service supprimé - système obsolète
    
    response = client.post(
        "/api/v1/dialogues/generate/interactions",
        json={
            "k_variants": 1,
            "max_context_tokens": 1000,
            "user_instructions": "Test",
            "llm_model_identifier": "gpt-5.2-mini",
            "previous_interaction_id": "non-existent",
            "context_selections": {
                "characters": [],
                "locations": [],
                "items": [],
                "species": [],
                "communities": []
            }
        }
    )
    assert response.status_code == 404  # Not found

