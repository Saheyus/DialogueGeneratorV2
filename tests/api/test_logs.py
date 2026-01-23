"""Tests pour les endpoints de logs."""
import json
import pytest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app
from api.services.log_service import LogService


@pytest.fixture
def client():
    """Crée un client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def sample_logs(tmp_path):
    """Crée des fichiers de logs d'exemple."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    # Créer des logs pour différentes dates
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Logs d'aujourd'hui
    today_file = log_dir / f"logs_{today.isoformat()}.json"
    today_logs = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": "INFO",
            "logger": "api.middleware",
            "message": "Request: GET /api/test",
            "request_id": "req1",
            "endpoint": "/api/test",
            "method": "GET",
            "status_code": 200
        },
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat() + "Z",
            "level": "ERROR",
            "logger": "api.routers",
            "message": "Error in endpoint",
            "request_id": "req2",
            "endpoint": "/api/error",
            "method": "POST"
        }
    ]
    with open(today_file, 'w', encoding='utf-8') as f:
        json.dump(today_logs, f)
    
    # Logs d'hier
    yesterday_file = log_dir / f"logs_{yesterday.isoformat()}.json"
    yesterday_logs = [
        {
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat() + "Z",
            "level": "WARNING",
            "logger": "api.middleware",
            "message": "Slow request",
            "request_id": "req3",
            "endpoint": "/api/slow",
            "method": "GET",
            "duration_ms": 5000
        }
    ]
    with open(yesterday_file, 'w', encoding='utf-8') as f:
        json.dump(yesterday_logs, f)
    
    return log_dir


def test_search_logs_all(client, sample_logs, monkeypatch):
    """Teste la recherche de logs sans filtres."""
    # Override la dépendance pour utiliser le dossier de test
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        response = client.get("/api/v1/logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert len(data["logs"]) > 0
    finally:
        logs.get_log_service = original_get


def test_search_logs_by_level(client, sample_logs, monkeypatch):
    """Teste la recherche de logs par niveau."""
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        response = client.get("/api/v1/logs?level=ERROR")
        assert response.status_code == 200
        data = response.json()
        assert all(log["level"] == "ERROR" for log in data["logs"])
    finally:
        logs.get_log_service = original_get


def test_search_logs_by_request_id(client, sample_logs, monkeypatch):
    """Teste la recherche de logs par request_id."""
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        response = client.get("/api/v1/logs?request_id=req1")
        assert response.status_code == 200
        data = response.json()
        assert all(log.get("request_id") == "req1" for log in data["logs"])
    finally:
        logs.get_log_service = original_get


def test_get_log_statistics(client, sample_logs, monkeypatch):
    """Teste l'endpoint de statistiques."""
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        response = client.get("/api/v1/logs/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data
        assert "by_level" in data
        assert "by_day" in data
        assert "by_logger" in data
        assert data["total_logs"] > 0
    finally:
        logs.get_log_service = original_get


def test_list_log_files(client, sample_logs, monkeypatch):
    """Teste l'endpoint de liste des fichiers."""
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        response = client.get("/api/v1/logs/files")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "filename" in data[0]
        assert "date" in data[0]
        assert "size_bytes" in data[0]
    finally:
        logs.get_log_service = original_get


def test_receive_frontend_log(client, sample_logs, monkeypatch):
    """Teste l'endpoint de réception de logs frontend."""
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        response = client.post(
            "/api/v1/logs/frontend",
            json={
                "level": "ERROR",
                "message": "Frontend error",
                "logger": "frontend.component",
                "error": {
                    "name": "TypeError",
                    "message": "Cannot read property"
                },
                "context": {
                    "url": "/test",
                    "userAgent": "Mozilla/5.0"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    finally:
        logs.get_log_service = original_get


def test_search_logs_pagination(client, sample_logs, monkeypatch):
    """Teste la pagination des résultats."""
    def get_test_log_service():
        return LogService(log_dir=str(sample_logs))
    
    from api.routers import logs
    original_get = logs.get_log_service
    logs.get_log_service = get_test_log_service
    
    try:
        # Première page
        response1 = client.get("/api/v1/logs?limit=1&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["logs"]) == 1
        assert data1["total"] > 1
        
        # Deuxième page
        response2 = client.get("/api/v1/logs?limit=1&offset=1")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["logs"]) == 1
        # Les logs doivent être différents
        assert data1["logs"][0]["timestamp"] != data2["logs"][0]["timestamp"]
    finally:
        logs.get_log_service = original_get


