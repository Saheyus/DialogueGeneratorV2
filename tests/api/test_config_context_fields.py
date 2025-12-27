"""Tests pour les endpoints API de configuration des champs de contexte."""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from context_builder import ContextBuilder


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_context_builder(monkeypatch):
    """Mock du ContextBuilder avec des données de test."""
    builder = ContextBuilder()
    
    # Ajouter des données de test
    builder.characters = [
        {
            "Nom": "Test Character",
            "Dialogue Type": {
                "Registre de langage du personnage": "Formel",
                "Champs lexicaux utilisés": ["Test", "Lexical"]
            },
            "Caractérisation": {
                "Désir": "Test desire",
                "Faiblesse": "Test weakness"
            }
        }
    ]
    builder.locations = [
        {
            "Nom": "Test Location",
            "Rôle": "Test role"
        }
    ]
    
    return builder


class TestContextFieldsEndpoints:
    """Tests pour les endpoints de champs de contexte."""
    
    def test_get_context_fields_character(self, client, mock_context_builder, monkeypatch):
        """Test de récupération des champs pour un personnage."""
        from api.dependencies import get_context_builder
        
        def mock_get_context_builder():
            return mock_context_builder
        
        monkeypatch.setattr("api.dependencies.get_context_builder", mock_get_context_builder)
        
        response = client.get("/api/v1/config/context-fields/character")
        
        assert response.status_code == 200
        data = response.json()
        assert "element_type" in data
        assert "fields" in data
        assert "total" in data
        assert data["element_type"] == "character"
        assert isinstance(data["fields"], dict)
        assert data["total"] > 0
    
    def test_get_context_fields_location(self, client, mock_context_builder, monkeypatch):
        """Test de récupération des champs pour un lieu."""
        from api.dependencies import get_context_builder
        
        def mock_get_context_builder():
            return mock_context_builder
        
        monkeypatch.setattr("api.dependencies.get_context_builder", mock_get_context_builder)
        
        response = client.get("/api/v1/config/context-fields/location")
        
        assert response.status_code == 200
        data = response.json()
        assert data["element_type"] == "location"
        assert isinstance(data["fields"], dict)
    
    def test_get_field_suggestions(self, client, mock_context_builder, monkeypatch):
        """Test de récupération des suggestions de champs."""
        from api.dependencies import get_context_builder
        
        def mock_get_context_builder():
            return mock_context_builder
        
        monkeypatch.setattr("api.dependencies.get_context_builder", mock_get_context_builder)
        
        response = client.post(
            "/api/v1/config/context-fields/suggestions",
            json={
                "element_type": "character",
                "context": "dialogue"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "element_type" in data
        assert "suggested_fields" in data
        assert data["element_type"] == "character"
        assert isinstance(data["suggested_fields"], list)
    
    def test_preview_context(self, client, mock_context_builder, monkeypatch):
        """Test de prévisualisation du contexte."""
        from api.dependencies import get_context_builder
        
        def mock_get_context_builder():
            return mock_context_builder
        
        monkeypatch.setattr("api.dependencies.get_context_builder", mock_get_context_builder)
        
        response = client.post(
            "/api/v1/config/context-fields/preview",
            json={
                "selected_elements": {
                    "characters": ["Test Character"]
                },
                "field_configs": {
                    "character": ["Nom", "Dialogue Type"]
                },
                "organization_mode": "default",
                "scene_instruction": "Test scene",
                "max_tokens": 1000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "preview" in data
        assert "tokens" in data
        assert isinstance(data["preview"], str)
        assert isinstance(data["tokens"], int)
        assert data["tokens"] > 0

