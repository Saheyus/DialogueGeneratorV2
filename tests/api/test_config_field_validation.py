"""Tests pour l'endpoint API de validation des champs."""
import pytest
from fastapi.testclient import TestClient
from core.context.context_builder import ContextBuilder
from unittest.mock import MagicMock


@pytest.fixture
def client():
    """Client de test FastAPI."""
    from api.main import app
    return TestClient(app)


@pytest.fixture
def mock_context_builder(monkeypatch):
    """Mock du ContextBuilder avec des données de test."""
    # Créer un mock pour GDDDataAccessor
    mock_accessor = MagicMock()
    mock_accessor.characters = [
        {
            "Nom": "Test Character",
            "Introduction": {
                "Résumé de la fiche": "Test summary"
            },
            "Registre de langage du personnage": "Formel",
            "Expressions courantes": ["Test"]
        }
    ]
    mock_accessor.locations = []
    mock_accessor.items = []
    mock_accessor.species = []
    mock_accessor.communities = []
    mock_accessor.quests = []
    
    # Créer un ContextBuilder avec le mock injecté
    builder = ContextBuilder()
    builder._gdd_data_accessor = mock_accessor
    
    return builder


class TestFieldValidationEndpoint:
    """Tests pour l'endpoint de validation des champs."""
    
    def test_validate_context_fields_endpoint(self, client, mock_context_builder, monkeypatch):
        """Test de l'endpoint /context-fields/validate."""
        from api.dependencies import get_context_builder, get_config_service
        from services.configuration_service import ConfigurationService
        
        def mock_get_context_builder():
            return mock_context_builder
        
        def mock_get_config_service():
            service = ConfigurationService()
            # Mock de la config avec des champs valides et invalides
            service.context_config = {
                "character": {
                    "1": [
                        {"path": "Nom", "label": "Nom"},
                        {"path": "InvalidField", "label": "Invalid"}
                    ]
                }
            }
            return service
        
        monkeypatch.setattr("api.dependencies.get_context_builder", mock_get_context_builder)
        monkeypatch.setattr("api.dependencies.get_config_service", mock_get_config_service)
        
        response = client.get("/api/v1/config/context-fields/validate")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "results" in data
        assert "text_report" in data
        
        assert "total_element_types" in data["summary"]
        assert "total_errors" in data["summary"]
        assert "total_warnings" in data["summary"]
    
    def test_context_fields_with_validation_flags(self, client, mock_context_builder, monkeypatch):
        """Test que les flags is_in_config et is_valid sont présents."""
        from api.dependencies import get_context_builder, get_config_service
        from services.configuration_service import ConfigurationService
        
        def mock_get_context_builder():
            return mock_context_builder
        
        def mock_get_config_service():
            service = ConfigurationService()
            service.context_config = {
                "character": {
                    "1": [
                        {"path": "Nom", "label": "Nom"},
                        {"path": "Introduction.Résumé de la fiche", "label": "Résumé"}
                    ]
                }
            }
            return service
        
        monkeypatch.setattr("api.dependencies.get_context_builder", mock_get_context_builder)
        monkeypatch.setattr("api.dependencies.get_config_service", mock_get_config_service)
        
        response = client.get("/api/v1/config/context-fields/character")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier que les flags sont présents dans au moins un champ
        if data["fields"]:
            first_field = list(data["fields"].values())[0]
            assert "is_in_config" in first_field
            assert "is_valid" in first_field
            assert isinstance(first_field["is_in_config"], bool)
            assert isinstance(first_field["is_valid"], bool)
