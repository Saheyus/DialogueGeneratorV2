"""Tests pour le middleware de cost governance."""
import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from api.middleware.cost_governance import CostGovernanceMiddleware
from services.cost_governance_service import CostGovernanceService
from services.repositories.cost_budget_repository import FileCostBudgetRepository


# Note: Les apps de test sont créées dans chaque fixture pour éviter les conflits


@pytest.fixture
def temp_budget_file(tmp_path):
    """Crée un fichier de budget temporaire."""
    return tmp_path / "cost_budgets.json"


# Fixture supprimée - chaque test crée son propre client


def test_middleware_allows_under_budget(temp_budget_file):
    """Teste que le middleware autorise les requêtes sous le budget."""
    # Créer le repository et le service
    repository = FileCostBudgetRepository(storage_file=str(temp_budget_file))
    cost_service = CostGovernanceService(repository=repository)
    
    # Configurer un budget (0€ dépensés sur 100€)
    cost_service.update_quota("default_user", 100.0)
    
    # Créer l'app de test avec le middleware
    test_app = FastAPI()
    test_app.add_middleware(CostGovernanceMiddleware)
    
    @test_app.post("/api/v1/dialogues/generate/unity-dialogue")
    async def test_generate():
        return JSONResponse(content={"status": "generated"})
    
    # Mock get_cost_budget_repository pour utiliser le repository temporaire
    with patch("api.middleware.cost_governance.get_cost_budget_repository", return_value=repository):
        client = TestClient(test_app)
        
        # Budget: 0€ dépensés sur 100€ (0%)
        response = client.post(
            "/api/v1/dialogues/generate/unity-dialogue",
            json={"test": "data"}
        )
        
        # Devrait être autorisé (pas de blocage)
        assert response.status_code == 200
        assert response.json()["status"] == "generated"


def test_middleware_blocks_at_100_percent(temp_budget_file):
    """Teste que le middleware bloque à 100% du budget."""
    from datetime import datetime
    
    # Configurer le budget à 100€ dépensés sur 100€ (100%)
    repository = FileCostBudgetRepository(storage_file=str(temp_budget_file))
    current_month = datetime.now().strftime("%Y-%m")
    repository.update_budget("default_user", current_month, 100.0, 100.0)
    
    # Créer l'app de test avec le middleware
    test_app = FastAPI()
    test_app.add_middleware(CostGovernanceMiddleware)
    
    @test_app.post("/api/v1/dialogues/generate/unity-dialogue")
    async def test_generate():
        return JSONResponse(content={"status": "generated"})
    
    # Mock get_cost_budget_repository pour utiliser le repository temporaire
    with patch("api.middleware.cost_governance.get_cost_budget_repository", return_value=repository):
        client = TestClient(test_app)
        
        # Tenter une génération
        response = client.post(
            "/api/v1/dialogues/generate/unity-dialogue",
            json={"test": "data"}
        )
        
        # Devrait être bloqué avec HTTP 429
        assert response.status_code == 429
        assert "error" in response.json()
        assert response.json()["error"]["code"] == "QUOTA_EXCEEDED"


def test_middleware_warns_at_90_percent(temp_budget_file):
    """Teste que le middleware affiche un warning à 90% mais autorise."""
    from datetime import datetime
    
    # Configurer le budget à 90€ dépensés sur 100€ (90%)
    repository = FileCostBudgetRepository(storage_file=str(temp_budget_file))
    current_month = datetime.now().strftime("%Y-%m")
    repository.update_budget("default_user", current_month, 90.0, 100.0)
    
    # Créer l'app de test avec le middleware
    test_app = FastAPI()
    test_app.add_middleware(CostGovernanceMiddleware)
    
    @test_app.post("/api/v1/dialogues/generate/unity-dialogue")
    async def test_generate():
        return JSONResponse(content={"status": "generated"})
    
    # Mock get_cost_budget_repository pour utiliser le repository temporaire
    with patch("api.middleware.cost_governance.get_cost_budget_repository", return_value=repository):
        client = TestClient(test_app)
        
        # Tenter une génération
        response = client.post(
            "/api/v1/dialogues/generate/unity-dialogue",
            json={"test": "data"}
        )
        
        # Devrait être autorisé (pas de blocage) mais avec warning loggé
        assert response.status_code == 200
        assert response.json()["status"] == "generated"


def test_middleware_ignores_non_generation_endpoints():
    """Teste que le middleware ignore les endpoints non-génération."""
    test_app = FastAPI()
    test_app.add_middleware(CostGovernanceMiddleware)
    
    @test_app.get("/api/v1/other-endpoint")
    async def test_other():
        return JSONResponse(content={"status": "ok"})
    
    client = TestClient(test_app)
    
    # Requête GET vers un endpoint non-génération
    response = client.get("/api/v1/other-endpoint")
    
    # Devrait passer sans vérification budget
    assert response.status_code == 200
