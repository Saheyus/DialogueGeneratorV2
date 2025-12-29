"""Tests pour le repository d'utilisation LLM."""
import pytest
from pathlib import Path
from datetime import date, datetime, timedelta, UTC
from models.llm_usage import LLMUsageRecord
from services.repositories.llm_usage_repository import FileLLMUsageRepository


@pytest.fixture
def repository(tmp_path):
    """Crée un repository temporaire."""
    return FileLLMUsageRepository(storage_dir=str(tmp_path))


@pytest.fixture
def sample_record():
    """Crée un enregistrement d'exemple."""
    return LLMUsageRecord(
        request_id="req_123",
        timestamp=datetime.now(UTC),
        model_name="gpt-5.2",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        estimated_cost=0.005,
        duration_ms=2500,
        success=True,
        endpoint="generate/variants",
        k_variants=3
    )


def test_save_and_load(repository, sample_record):
    """Teste la sauvegarde et le chargement d'un enregistrement."""
    repository.save(sample_record)
    
    records = repository.get_all()
    assert len(records) == 1
    assert records[0].request_id == sample_record.request_id
    assert records[0].model_name == sample_record.model_name


def test_get_by_date_range(repository, sample_record):
    """Teste la récupération par plage de dates."""
    # Créer des enregistrements pour différentes dates
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    record_today = sample_record.model_copy()
    record_today.timestamp = datetime.combine(today, datetime.min.time())
    
    record_yesterday = sample_record.model_copy()
    record_yesterday.request_id = "req_456"
    record_yesterday.timestamp = datetime.combine(yesterday, datetime.min.time())
    
    repository.save(record_today)
    repository.save(record_yesterday)
    
    # Récupérer seulement aujourd'hui
    records = repository.get_by_date_range(today, today)
    assert len(records) == 1
    assert records[0].request_id == "req_123"
    
    # Récupérer les deux jours
    records = repository.get_by_date_range(yesterday, today)
    assert len(records) == 2


def test_get_statistics(repository, sample_record):
    """Teste le calcul des statistiques."""
    # Créer plusieurs enregistrements
    for i in range(5):
        record = sample_record.model_copy()
        record.request_id = f"req_{i}"
        record.total_tokens = 1000 + i * 100
        record.estimated_cost = 0.001 * (i + 1)
        record.success = i < 4  # 4 réussis, 1 échec
        repository.save(record)
    
    stats = repository.get_statistics()
    assert stats["calls_count"] == 5
    assert stats["success_count"] == 4
    assert stats["error_count"] == 1
    assert stats["success_rate"] == 80.0
    assert stats["total_tokens"] > 0
    assert stats["total_cost"] > 0


def test_filter_by_model(repository, sample_record):
    """Teste le filtrage par modèle."""
    record_gpt4 = sample_record.model_copy()
    record_gpt35 = sample_record.model_copy()
    record_gpt35.request_id = "req_456"
    record_gpt35.model_name = "gpt-3.5-turbo"
    
    repository.save(record_gpt4)
    repository.save(record_gpt35)
    
    records = repository.get_all(model_name="gpt-4o")
    assert len(records) == 1
    assert records[0].model_name == "gpt-4o"

