"""Tests pour les endpoints de suivi LLM."""
import pytest
from datetime import date, datetime, timedelta, UTC
from fastapi.testclient import TestClient
from models.llm_usage import LLMUsageRecord
from services.llm_usage_service import LLMUsageService
from services.repositories.llm_usage_repository import FileLLMUsageRepository
from services.llm_pricing_service import LLMPricingService
from api.main import app
from api.dependencies import get_llm_usage_service


@pytest.fixture
def client():
    """Crée un client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def sample_records():
    """Crée des enregistrements d'exemple."""
    base_time = datetime.now(UTC)
    return [
        LLMUsageRecord(
            request_id=f"req_{i}",
            timestamp=base_time - timedelta(hours=i),
            model_name="gpt-5.2" if i % 2 == 0 else "gpt-3.5-turbo",
            prompt_tokens=1000 + i * 100,
            completion_tokens=500 + i * 50,
            total_tokens=1500 + i * 150,
            estimated_cost=0.005 + i * 0.001,
            duration_ms=2500 + i * 100,
            success=i < 8,  # 8 réussis, 2 échecs
            endpoint="generate/variants",
            k_variants=3
        )
        for i in range(10)
    ]


def test_get_usage_history(client, sample_records, tmp_path):
    """Teste l'endpoint GET /api/v1/llm-usage/history."""
    # Créer un repository temporaire et y ajouter des enregistrements
    repository = FileLLMUsageRepository(storage_dir=str(tmp_path))
    for record in sample_records:
        repository.save(record)
    
    # Override la dépendance FastAPI
    test_service = LLMUsageService(
        repository=repository,
        pricing_service=LLMPricingService()
    )
    app.dependency_overrides[get_llm_usage_service] = lambda: test_service
    
    try:
        # Faire la requête
        response = client.get("/api/v1/llm-usage/history?page=1&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert "page" in data
        assert len(data["records"]) == 5
        assert data["total"] == 10
    finally:
        # Nettoyer l'override
        app.dependency_overrides.pop(get_llm_usage_service, None)


def test_get_usage_statistics(client, sample_records, tmp_path):
    """Teste l'endpoint GET /api/v1/llm-usage/statistics."""
    # Créer un repository temporaire et y ajouter des enregistrements
    repository = FileLLMUsageRepository(storage_dir=str(tmp_path))
    for record in sample_records:
        repository.save(record)
    
    # Override la dépendance FastAPI
    test_service = LLMUsageService(
        repository=repository,
        pricing_service=LLMPricingService()
    )
    app.dependency_overrides[get_llm_usage_service] = lambda: test_service
    
    try:
        # Faire la requête
        response = client.get("/api/v1/llm-usage/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tokens" in data
        assert "total_cost" in data
        assert "calls_count" in data
        assert "success_rate" in data
        assert data["calls_count"] == 10
    finally:
        # Nettoyer l'override
        app.dependency_overrides.pop(get_llm_usage_service, None)


def test_get_usage_history_with_filters(client, sample_records, tmp_path):
    """Teste l'endpoint avec filtres (date, modèle)."""
    repository = FileLLMUsageRepository(storage_dir=str(tmp_path))
    for record in sample_records:
        repository.save(record)
    
    # Override la dépendance FastAPI
    test_service = LLMUsageService(
        repository=repository,
        pricing_service=LLMPricingService()
    )
    app.dependency_overrides[get_llm_usage_service] = lambda: test_service
    
    try:
        # Filtrer par modèle
        response = client.get("/api/v1/llm-usage/history?model=gpt-5.2&page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        # Vérifier que tous les enregistrements sont pour gpt-5.2
        for record in data["records"]:
            assert record["model_name"] == "gpt-5.2"
    finally:
        # Nettoyer l'override
        app.dependency_overrides.pop(get_llm_usage_service, None)

