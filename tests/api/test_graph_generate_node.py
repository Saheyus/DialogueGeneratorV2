"""Tests pour l'endpoint /api/v1/graph/generate-node."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from api.main import app
from api.dependencies import get_config_service
from services.configuration_service import ConfigurationService


@pytest.fixture
def mock_config_service():
    """Mock du ConfigurationService."""
    mock_service = MagicMock(spec=ConfigurationService)
    return mock_service


@pytest.fixture
def client(mock_config_service):
    """Fixture pour créer un client de test avec mocks."""
    app.dependency_overrides[get_config_service] = lambda: mock_config_service
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_parent_node_with_choices():
    """Nœud parent avec choix pour les tests."""
    return {
        "id": "NODE_PARENT_1",
        "speaker": "PNJ",
        "line": "Bonjour, comment allez-vous ?",
        "choices": [
            {"text": "Je vais bien", "targetNode": None},
            {"text": "Pas très bien", "targetNode": None},
            {"text": "Je ne sais pas", "targetNode": "END"}
        ]
    }


@pytest.fixture
def sample_parent_node_without_choices():
    """Nœud parent sans choix (navigation linéaire)."""
    return {
        "id": "NODE_PARENT_2",
        "speaker": "PNJ",
        "line": "Voici une information importante.",
        "nextNode": None
    }


@pytest.mark.asyncio
async def test_generate_node_with_target_choice_index(client, sample_parent_node_with_choices):
    """Test génération nœud pour choix spécifique (target_choice_index).
    
    AC: #1 - Génération pour choix spécifique depuis éditeur de graphe.
    """
    with patch('factories.llm_factory.LLMClientFactory') as mock_factory, \
         patch('api.routers.graph.ServiceContainer') as mock_container, \
         patch('api.routers.graph.UnityDialogueGenerationService') as mock_service_class:
        
        # Setup mocks
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock de la génération
        mock_node = {
            "id": "NODE_PARENT_1_CHOICE_0",
            "speaker": "PNJ",
            "line": "Je suis content de l'entendre !",
            "choices": []
        }
        mock_service.enrich_with_ids.return_value = [mock_node]
        mock_service.generate_dialogue_node = AsyncMock(return_value={"nodes": [mock_node]})
        
        # Mock LLM client
        mock_llm_client = MagicMock()
        mock_factory.create_client.return_value = mock_llm_client
        
        # Mock config service
        mock_config_service = MagicMock()
        mock_config_service.get_llm_config.return_value = {}
        mock_config_service.get_available_llm_models.return_value = []
        mock_container_instance = MagicMock()
        mock_container_instance.get_config_service.return_value = mock_config_service
        mock_container.return_value = mock_container_instance
        
        request_data = {
            "parent_node_id": "NODE_PARENT_1",
            "parent_node_content": sample_parent_node_with_choices,
            "user_instructions": "Continue la conversation",
            "context_selections": {},
            "target_choice_index": 0,  # Nouveau paramètre
            "generate_all_choices": False
        }
        
        response = client.post("/api/v1/unity-dialogues/graph/generate-node", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "node" in data
        assert data["node"]["id"] == "NODE_PARENT_1_CHOICE_0"
        assert "suggested_connections" in data
        # Vérifier que la connexion suggérée utilise via_choice_index=0
        assert len(data["suggested_connections"]) > 0
        assert data["suggested_connections"][0]["via_choice_index"] == 0


@pytest.mark.asyncio
async def test_generate_node_with_generate_all_choices(client, sample_parent_node_with_choices):
    """Test génération batch pour tous les choix (generate_all_choices=True).
    
    AC: #3 - Génération batch pour tous les choix depuis éditeur de graphe.
    """
    with patch('factories.llm_factory.LLMClientFactory') as mock_factory, \
         patch('api.routers.graph.ServiceContainer') as mock_container, \
         patch('api.routers.graph.GraphGenerationService') as mock_graph_service_class, \
         patch('api.routers.graph.UnityDialogueGenerationService') as mock_service_class:
        
        # Setup mocks
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock GraphGenerationService pour batch
        mock_graph_service = MagicMock()
        mock_graph_service_class.return_value = mock_graph_service
        
        # Mock résultat batch (2 choix sans targetNode)
        mock_batch_result = {
            "nodes": [
                {"id": "NODE_PARENT_1_CHOICE_0", "speaker": "PNJ", "line": "Réponse 1", "choices": []},
                {"id": "NODE_PARENT_1_CHOICE_1", "speaker": "PNJ", "line": "Réponse 2", "choices": []}
            ],
            "connections": [
                {"from": "NODE_PARENT_1", "to": "NODE_PARENT_1_CHOICE_0", "via_choice_index": 0, "connection_type": "choice"},
                {"from": "NODE_PARENT_1", "to": "NODE_PARENT_1_CHOICE_1", "via_choice_index": 1, "connection_type": "choice"}
            ]
        }
        mock_graph_service.generate_nodes_for_all_choices = AsyncMock(return_value=mock_batch_result)
        
        # Mock LLM client
        mock_llm_client = MagicMock()
        mock_factory.create_client.return_value = mock_llm_client
        
        # Mock config service
        mock_config_service = MagicMock()
        mock_config_service.get_llm_config.return_value = {}
        mock_config_service.get_available_llm_models.return_value = []
        mock_container_instance = MagicMock()
        mock_container_instance.get_config_service.return_value = mock_config_service
        mock_container.return_value = mock_container_instance
        
        request_data = {
            "parent_node_id": "NODE_PARENT_1",
            "parent_node_content": sample_parent_node_with_choices,
            "user_instructions": "Continue la conversation",
            "context_selections": {},
            "target_choice_index": None,
            "generate_all_choices": True  # Nouveau paramètre
        }
        
        response = client.post("/api/v1/unity-dialogues/graph/generate-node", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        # Vérifier que le service batch a été appelé
        mock_graph_service.generate_nodes_for_all_choices.assert_called_once()
        # Vérifier que le premier nœud est retourné
        assert "node" in data
        assert data["node"]["id"] == "NODE_PARENT_1_CHOICE_0"
        # Vérifier que les connexions sont retournées
        assert len(data["suggested_connections"]) == 2


@pytest.mark.asyncio
async def test_generate_node_nextnode_linear(client, sample_parent_node_without_choices):
    """Test génération nextNode pour navigation linéaire.
    
    AC: #5 - Génération nextNode depuis éditeur de graphe.
    """
    with patch('factories.llm_factory.LLMClientFactory') as mock_factory, \
         patch('api.routers.graph.ServiceContainer') as mock_container, \
         patch('api.routers.graph.UnityDialogueGenerationService') as mock_service_class:
        
        # Setup mocks
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        mock_node = {
            "id": "NODE_PARENT_2_CHILD",
            "speaker": "PNJ",
            "line": "Suite de la conversation",
            "nextNode": None
        }
        mock_service.enrich_with_ids.return_value = [mock_node]
        mock_service.generate_dialogue_node = AsyncMock(return_value={"nodes": [mock_node]})
        
        # Mock LLM client
        mock_llm_client = MagicMock()
        mock_factory.create_client.return_value = mock_llm_client
        
        # Mock config service
        mock_config_service = MagicMock()
        mock_config_service.get_llm_config.return_value = {}
        mock_config_service.get_available_llm_models.return_value = []
        mock_container_instance = MagicMock()
        mock_container_instance.get_config_service.return_value = mock_config_service
        mock_container.return_value = mock_container_instance
        
        request_data = {
            "parent_node_id": "NODE_PARENT_2",
            "parent_node_content": sample_parent_node_without_choices,
            "user_instructions": "Continue la conversation",
            "context_selections": {},
            "target_choice_index": None,
            "generate_all_choices": False
        }
        
        response = client.post("/api/v1/unity-dialogues/graph/generate-node", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "node" in data
        assert "suggested_connections" in data
        # Vérifier que la connexion suggérée est de type nextNode
        assert len(data["suggested_connections"]) > 0
        assert data["suggested_connections"][0]["connection_type"] == "nextNode"
