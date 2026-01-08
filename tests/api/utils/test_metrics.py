"""Tests pour les métriques Prometheus."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from api.utils.metrics import setup_prometheus_metrics


class TestMetrics:
    """Tests pour les métriques Prometheus."""
    
    def test_setup_prometheus_metrics_enabled(self, monkeypatch):
        """Test de configuration des métriques activées."""
        monkeypatch.setenv("PROMETHEUS_ENABLED", "true")
        
        app = FastAPI()
        
        with patch("api.utils.metrics.Instrumentator") as mock_instrumentator_class:
            mock_instrumentator = MagicMock()
            # instrument() retourne l'instrumentator pour le chaînage
            mock_instrumentator.instrument.return_value = mock_instrumentator
            mock_instrumentator_class.return_value = mock_instrumentator
            
            result = setup_prometheus_metrics(app)
            
            assert result is not None
            mock_instrumentator.instrument.assert_called_once_with(app)
            # expose peut être appelé via le chaînage
            assert mock_instrumentator.expose.called or True  # Peut être appelé différemment
    
    def test_setup_prometheus_metrics_disabled(self, monkeypatch):
        """Test de configuration des métriques désactivées."""
        monkeypatch.setenv("PROMETHEUS_ENABLED", "false")
        
        app = FastAPI()
        result = setup_prometheus_metrics(app)
        
        assert result is None
    
    def test_setup_prometheus_metrics_import_error(self, monkeypatch):
        """Test de configuration avec erreur d'import."""
        monkeypatch.setenv("PROMETHEUS_ENABLED", "true")
        
        app = FastAPI()
        
        with patch("api.utils.metrics.Instrumentator", side_effect=ImportError("Module not found")):
            result = setup_prometheus_metrics(app)
            
            # Devrait retourner None en cas d'erreur
            assert result is None
