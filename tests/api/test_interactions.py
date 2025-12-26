"""Tests pour les endpoints d'interactions (CRUD)."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from services.interaction_service import InteractionService
from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dialogue_elements import (
    DialogueLineElement,
    PlayerChoicesBlockElement,
    PlayerChoiceOption
)


@pytest.fixture
def mock_interaction_service():
    """Mock du InteractionService."""
    mock_service = MagicMock(spec=InteractionService)
    
    # Interaction de test
    test_interaction = Interaction(
        interaction_id="test-1",
        title="Test Interaction",
        elements=[DialogueLineElement(text="Hello", speaker="NPC")]
    )
    
    mock_service.get_all = MagicMock(return_value=[test_interaction])
    mock_service.get_by_id = MagicMock(return_value=test_interaction)
    mock_service.exists = MagicMock(return_value=True)
    mock_service.create_interaction = MagicMock(return_value=test_interaction)
    mock_service.save = MagicMock()
    mock_service.delete = MagicMock()
    mock_service.get_parent_interactions = MagicMock(return_value=[])
    mock_service.get_child_interactions = MagicMock(return_value=[])
    mock_service.get_dialogue_path = MagicMock(return_value=[test_interaction])
    
    return mock_service


@pytest.fixture
def client(mock_interaction_service):
    """Fixture pour créer un client de test avec mocks."""
    from api.dependencies import get_interaction_service
    
    # Override la dépendance FastAPI
    app.dependency_overrides[get_interaction_service] = lambda: mock_interaction_service
    
    yield TestClient(app)
    
    # Nettoyer après le test
    app.dependency_overrides.clear()


def test_list_interactions(client, mock_interaction_service):
    """Test de liste des interactions."""
    response = client.get("/api/v1/interactions")
    assert response.status_code == 200
    data = response.json()
    assert "interactions" in data
    assert "total" in data
    assert isinstance(data["total"], int)
    assert isinstance(data["interactions"], list)


def test_get_interaction(client, mock_interaction_service):
    """Test de récupération d'une interaction."""
    response = client.get("/api/v1/interactions/test-1")
    assert response.status_code == 200
    data = response.json()
    assert "interaction_id" in data
    assert data["interaction_id"] == "test-1"
    assert "title" in data


def test_get_interaction_not_found(client, mock_interaction_service):
    """Test de récupération d'une interaction inexistante."""
    mock_interaction_service.get_by_id = MagicMock(return_value=None)
    
    response = client.get("/api/v1/interactions/non-existent")
    assert response.status_code == 404


def test_create_interaction(client, mock_interaction_service):
    """Test de création d'une interaction."""
    new_interaction = Interaction(
        interaction_id="new-1",
        title="New Interaction",
        elements=[DialogueLineElement(text="New dialogue", speaker="NPC")]
    )
    mock_interaction_service.create_interaction = MagicMock(return_value=new_interaction)
    
    response = client.post(
        "/api/v1/interactions",
        json={
            "title": "New Interaction",
            "elements": [
                {
                    "element_type": "dialogue_line",
                    "text": "New dialogue",
                    "speaker": "NPC"
                }
            ],
            "header_commands": [],
            "header_tags": []
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "interaction_id" in data
    assert "title" in data


def test_create_interaction_invalid(client, mock_interaction_service):
    """Test de création d'une interaction avec données invalides."""
    mock_interaction_service.create_interaction = MagicMock(side_effect=ValueError("Invalid data"))
    
    response = client.post(
        "/api/v1/interactions",
        json={
            "title": "",
            "elements": []
        }
    )
    # Peut être 422 (validation) ou 400 (validation service)
    assert response.status_code in [400, 422]


def test_update_interaction(client, mock_interaction_service):
    """Test de mise à jour d'une interaction."""
    updated_interaction = Interaction(
        interaction_id="test-1",
        title="Updated Title",
        elements=[DialogueLineElement(text="Updated", speaker="NPC")]
    )
    mock_interaction_service.get_by_id = MagicMock(return_value=updated_interaction)
    
    response = client.put(
        "/api/v1/interactions/test-1",
        json={
            "title": "Updated Title"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


def test_update_interaction_not_found(client, mock_interaction_service):
    """Test de mise à jour d'une interaction inexistante."""
    mock_interaction_service.get_by_id = MagicMock(return_value=None)
    
    response = client.put(
        "/api/v1/interactions/non-existent",
        json={
            "title": "Updated"
        }
    )
    assert response.status_code == 404


def test_delete_interaction(client, mock_interaction_service):
    """Test de suppression d'une interaction."""
    response = client.delete("/api/v1/interactions/test-1")
    assert response.status_code == 204


def test_delete_interaction_not_found(client, mock_interaction_service):
    """Test de suppression d'une interaction inexistante."""
    mock_interaction_service.exists = MagicMock(return_value=False)
    
    response = client.delete("/api/v1/interactions/non-existent")
    assert response.status_code == 404


def test_get_interaction_parents(client, mock_interaction_service):
    """Test de récupération des parents d'une interaction."""
    response = client.get("/api/v1/interactions/test-1/parents")
    assert response.status_code == 200
    data = response.json()
    assert "parents" in data
    assert "children" in data
    assert isinstance(data["parents"], list)


def test_get_interaction_parents_not_found(client, mock_interaction_service):
    """Test de récupération des parents d'une interaction inexistante."""
    mock_interaction_service.exists = MagicMock(return_value=False)
    
    response = client.get("/api/v1/interactions/non-existent/parents")
    assert response.status_code == 404


def test_get_interaction_children(client, mock_interaction_service):
    """Test de récupération des enfants d'une interaction."""
    response = client.get("/api/v1/interactions/test-1/children")
    assert response.status_code == 200
    data = response.json()
    assert "parents" in data
    assert "children" in data
    assert isinstance(data["children"], list)


def test_get_interaction_children_not_found(client, mock_interaction_service):
    """Test de récupération des enfants d'une interaction inexistante."""
    mock_interaction_service.exists = MagicMock(return_value=False)
    
    response = client.get("/api/v1/interactions/non-existent/children")
    assert response.status_code == 404


def test_get_interaction_context_path(client, mock_interaction_service):
    """Test de récupération du chemin de contexte d'une interaction."""
    response = client.get("/api/v1/interactions/test-1/context-path")
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "total" in data
    assert isinstance(data["path"], list)
    assert isinstance(data["total"], int)


def test_get_interaction_context_path_not_found(client, mock_interaction_service):
    """Test de récupération du chemin de contexte d'une interaction inexistante."""
    mock_interaction_service.exists = MagicMock(return_value=False)
    
    response = client.get("/api/v1/interactions/non-existent/context-path")
    assert response.status_code == 404

