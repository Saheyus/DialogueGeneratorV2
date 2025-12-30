"""Tests pour le handler de fichier rotatif de logs."""
import json
import pytest
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from api.utils.log_file_handler import DateRotatingFileHandler


@pytest.fixture
def tmp_log_dir(tmp_path):
    """Crée un dossier temporaire pour les logs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def handler(tmp_log_dir):
    """Crée un handler de test."""
    handler = DateRotatingFileHandler(
        log_dir=str(tmp_log_dir),
        retention_days=30,
        max_file_size_mb=1  # 1MB pour les tests
    )
    yield handler
    handler.close()


def test_handler_creates_file(handler, tmp_log_dir):
    """Teste que le handler crée un fichier de log."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    logger.info("Test message")
    handler.flush()
    
    # Vérifier qu'un fichier a été créé
    today = date.today()
    expected_file = tmp_log_dir / f"logs_{today.isoformat()}.json"
    assert expected_file.exists()
    
    # Vérifier le contenu
    with open(expected_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
        assert len(logs) == 1
        assert logs[0]["message"] == "Test message"
        assert logs[0]["level"] == "INFO"


def test_handler_rotates_by_date(handler, tmp_log_dir, monkeypatch):
    """Teste que le handler fait une rotation au changement de jour."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Écrire un log aujourd'hui
    logger.info("Log today")
    handler.flush()
    
    # Simuler le jour suivant
    tomorrow = date.today() + timedelta(days=1)
    monkeypatch.setattr("api.utils.log_file_handler.date.today", lambda: tomorrow)
    
    # Écrire un autre log
    logger.info("Log tomorrow")
    handler.flush()
    
    # Vérifier qu'il y a deux fichiers
    log_files = list(tmp_log_dir.glob("logs_*.json"))
    assert len(log_files) == 2


def test_handler_handles_corrupted_file(handler, tmp_log_dir):
    """Teste que le handler gère les fichiers corrompus."""
    today = date.today()
    log_file = tmp_log_dir / f"logs_{today.isoformat()}.json"
    
    # Créer un fichier corrompu
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("invalid json{")
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Le handler devrait recréer le fichier
    logger.info("Test message")
    handler.flush()
    
    # Vérifier que le fichier est valide maintenant
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
        assert len(logs) == 1


def test_handler_cleanup_old_files(handler, tmp_log_dir):
    """Teste la suppression des fichiers anciens."""
    # Créer des fichiers de logs pour différentes dates
    old_date = date.today() - timedelta(days=35)
    recent_date = date.today() - timedelta(days=5)
    
    old_file = tmp_log_dir / f"logs_{old_date.isoformat()}.json"
    recent_file = tmp_log_dir / f"logs_{recent_date.isoformat()}.json"
    
    # Créer les fichiers
    with open(old_file, 'w', encoding='utf-8') as f:
        json.dump([{"message": "old"}], f)
    with open(recent_file, 'w', encoding='utf-8') as f:
        json.dump([{"message": "recent"}], f)
    
    # Nettoyer avec rétention de 30 jours
    deleted_count = handler.cleanup_old_files()
    
    # Vérifier que seul le fichier ancien a été supprimé
    assert deleted_count == 1
    assert not old_file.exists()
    assert recent_file.exists()


def test_handler_enriches_log_context(handler, tmp_log_dir):
    """Teste que le handler enrichit les logs avec le contexte."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Créer un record avec contexte
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.request_id = "req123"
    record.endpoint = "/api/test"
    record.method = "GET"
    
    handler.emit(record)
    handler.flush()
    
    # Vérifier le contenu
    today = date.today()
    log_file = tmp_log_dir / f"logs_{today.isoformat()}.json"
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
        assert logs[0]["request_id"] == "req123"
        assert logs[0]["endpoint"] == "/api/test"
        assert logs[0]["method"] == "GET"


