"""Tests pour le service de tracking d'utilisation LLM."""
import pytest
from datetime import date, datetime, timedelta, UTC
from unittest.mock import Mock, MagicMock
from services.llm_usage_service import LLMUsageService
from services.llm_pricing_service import LLMPricingService
from models.llm_usage import LLMUsageRecord


@pytest.fixture
def mock_repository():
    """Crée un repository mock."""
    return Mock()


@pytest.fixture
def mock_pricing_service():
    """Crée un service de pricing mock."""
    service = Mock(spec=LLMPricingService)
    service.calculate_cost.return_value = 0.005
    return service


@pytest.fixture
def usage_service(mock_repository, mock_pricing_service):
    """Crée un service de tracking avec mocks."""
    return LLMUsageService(
        repository=mock_repository,
        pricing_service=mock_pricing_service
    )


def test_track_usage(usage_service, mock_repository, mock_pricing_service):
    """Teste l'enregistrement d'un appel LLM."""
    usage_service.track_usage(
        request_id="req_123",
        model_name="gpt-5.2",
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        duration_ms=2500,
        success=True,
        endpoint="generate/variants",
        k_variants=3
    )
    
    # Vérifier que le pricing service a été appelé
    mock_pricing_service.calculate_cost.assert_called_once_with(
        model_name="gpt-5.2",
        prompt_tokens=1000,
        completion_tokens=500
    )
    
    # Vérifier que le repository a été appelé
    assert mock_repository.save.called
    saved_record = mock_repository.save.call_args[0][0]
    assert isinstance(saved_record, LLMUsageRecord)
    assert saved_record.request_id == "req_123"
    assert saved_record.model_name == "gpt-5.2"
    assert saved_record.total_tokens == 1500


def test_track_usage_with_error(usage_service, mock_repository):
    """Teste l'enregistrement d'un appel en erreur."""
    usage_service.track_usage(
        request_id="req_456",
        model_name="gpt-5.2",
        prompt_tokens=1000,
        completion_tokens=0,
        total_tokens=1000,
        duration_ms=1000,
        success=False,
        endpoint="generate/variants",
        k_variants=1,
        error_message="API Error"
    )
    
    saved_record = mock_repository.save.call_args[0][0]
    assert saved_record.success is False
    assert saved_record.error_message == "API Error"


def test_get_usage_history(usage_service, mock_repository):
    """Teste la récupération de l'historique."""
    # Mock des enregistrements
    mock_records = [
        LLMUsageRecord(
            request_id=f"req_{i}",
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
        for i in range(10)
    ]
    mock_repository.get_by_date_range.return_value = mock_records
    
    start_date = date.today() - timedelta(days=7)
    end_date = date.today()
    
    records = usage_service.get_usage_history(
        start_date=start_date,
        end_date=end_date
    )
    
    assert len(records) == 10
    mock_repository.get_by_date_range.assert_called_once_with(
        start_date=start_date,
        end_date=end_date,
        model_name=None
    )


def test_get_statistics(usage_service, mock_repository):
    """Teste le calcul des statistiques."""
    mock_stats = {
        "total_tokens": 15000,
        "total_prompt_tokens": 10000,
        "total_completion_tokens": 5000,
        "total_cost": 0.05,
        "calls_count": 10,
        "success_count": 9,
        "error_count": 1,
        "success_rate": 90.0,
        "avg_duration_ms": 2500.0
    }
    mock_repository.get_statistics.return_value = mock_stats
    
    stats = usage_service.get_statistics()
    
    assert stats["total_tokens"] == 15000
    assert stats["calls_count"] == 10
    assert stats["success_rate"] == 90.0

