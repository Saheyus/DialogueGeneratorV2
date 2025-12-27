"""Tests pour la pagination des interactions."""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from models.dialogue_structure.interaction import Interaction
from services.interaction_service import InteractionService


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def sample_interactions():
    """Crée des interactions de test."""
    interactions = []
    for i in range(15):
        interaction = Interaction(
            interaction_id=f"test_{i}",
            title=f"Test Interaction {i}",
            elements=[],
            header_commands=[],
            header_tags=[]
        )
        interactions.append(interaction)
    return interactions


@pytest.fixture
def mock_interaction_service(sample_interactions, mocker):
    """Mock du service d'interactions."""
    service = mocker.Mock(spec=InteractionService)
    service.get_all.return_value = sample_interactions
    return service


def test_list_interactions_no_pagination(client, mock_interaction_service, mocker):
    """Test list_interactions sans pagination (rétrocompatibilité)."""
    from api.dependencies import get_interaction_service
    
    mocker.patch("api.dependencies.get_interaction_service", return_value=mock_interaction_service)
    
    # Obtenir un token d'authentification
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Faire la requête sans pagination
    response = client.get(
        "/api/v1/interactions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "interactions" in data
    assert "total" in data
    assert data["total"] == 15
    assert len(data["interactions"]) == 15
    assert data["page"] is None
    assert data["page_size"] is None
    assert data["total_pages"] is None


def test_list_interactions_with_pagination_first_page(client, mock_interaction_service, mocker):
    """Test list_interactions avec pagination (première page)."""
    from api.dependencies import get_interaction_service
    
    mocker.patch("api.dependencies.get_interaction_service", return_value=mock_interaction_service)
    
    # Obtenir un token d'authentification
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Faire la requête avec pagination
    response = client.get(
        "/api/v1/interactions?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "interactions" in data
    assert "total" in data
    assert data["total"] == 15
    assert len(data["interactions"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total_pages"] == 3  # 15 items / 5 par page = 3 pages


def test_list_interactions_with_pagination_middle_page(client, mock_interaction_service, mocker):
    """Test list_interactions avec pagination (page du milieu)."""
    from api.dependencies import get_interaction_service
    
    mocker.patch("api.dependencies.get_interaction_service", return_value=mock_interaction_service)
    
    # Obtenir un token d'authentification
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Faire la requête avec pagination
    response = client.get(
        "/api/v1/interactions?page=2&page_size=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 5
    assert len(data["interactions"]) == 5


def test_list_interactions_with_pagination_last_page(client, mock_interaction_service, mocker):
    """Test list_interactions avec pagination (dernière page)."""
    from api.dependencies import get_interaction_service
    
    mocker.patch("api.dependencies.get_interaction_service", return_value=mock_interaction_service)
    
    # Obtenir un token d'authentification
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Faire la requête avec pagination (dernière page)
    response = client.get(
        "/api/v1/interactions?page=3&page_size=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 3
    assert data["page_size"] == 5
    assert len(data["interactions"]) == 5  # 15 items, page 3 = items 11-15


def test_list_interactions_pagination_page_size_limit(client, mock_interaction_service, mocker):
    """Test que page_size est limité à PAGINATION_MAX_PAGE_SIZE."""
    import os
    from api.dependencies import get_interaction_service
    
    mocker.patch("api.dependencies.get_interaction_service", return_value=mock_interaction_service)
    
    # Obtenir un token d'authentification
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Faire la requête avec page_size > max (100 par défaut)
    response = client.get(
        "/api/v1/interactions?page=1&page_size=200",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # page_size devrait être limité à 100
    assert data["page_size"] == 100

