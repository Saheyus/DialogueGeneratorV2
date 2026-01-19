"""Tests pour le repository de budgets LLM."""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from services.repositories.cost_budget_repository import FileCostBudgetRepository


@pytest.fixture
def temp_storage_file(tmp_path):
    """Crée un fichier de stockage temporaire."""
    return tmp_path / "cost_budgets.json"


@pytest.fixture
def budget_repository(temp_storage_file):
    """Crée un repository avec fichier temporaire."""
    return FileCostBudgetRepository(storage_file=str(temp_storage_file))


def test_get_budget_existing(budget_repository, temp_storage_file):
    """Teste get_budget avec budget existant."""
    # Setup: créer un budget existant
    data = {
        "budgets": {
            "user_1": {
                "month": "2026-01",
                "amount": 75.0,
                "quota": 100.0,
                "updated_at": datetime.now().isoformat()
            }
        }
    }
    temp_storage_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    budget = budget_repository.get_budget("user_1", "2026-01")
    
    assert budget is not None
    assert budget["month"] == "2026-01"
    assert budget["amount"] == 75.0
    assert budget["quota"] == 100.0


def test_get_budget_not_existing(budget_repository):
    """Teste get_budget avec budget inexistant."""
    budget = budget_repository.get_budget("user_unknown", "2026-01")
    assert budget is None


def test_get_budget_wrong_month(budget_repository, temp_storage_file):
    """Teste get_budget avec mois différent."""
    # Setup: créer un budget pour un mois différent
    data = {
        "budgets": {
            "user_1": {
                "month": "2025-12",
                "amount": 75.0,
                "quota": 100.0,
                "updated_at": datetime.now().isoformat()
            }
        }
    }
    temp_storage_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    budget = budget_repository.get_budget("user_1", "2026-01")
    
    # Devrait retourner None car le mois ne correspond pas
    assert budget is None


def test_update_budget_new_user(budget_repository, temp_storage_file):
    """Teste update_budget pour un nouvel utilisateur."""
    budget_repository.update_budget("user_1", "2026-01", 50.0, 100.0)
    
    # Vérifier que le fichier a été créé
    assert temp_storage_file.exists()
    
    # Vérifier le contenu
    data = json.loads(temp_storage_file.read_text(encoding='utf-8'))
    user_budget = data["budgets"]["user_1"]
    assert user_budget["month"] == "2026-01"
    assert user_budget["amount"] == 50.0
    assert user_budget["quota"] == 100.0


def test_update_budget_existing_user(budget_repository, temp_storage_file):
    """Teste update_budget pour un utilisateur existant."""
    # Setup: créer un budget existant
    data = {
        "budgets": {
            "user_1": {
                "month": "2026-01",
                "amount": 50.0,
                "quota": 100.0,
                "updated_at": datetime.now().isoformat()
            }
        }
    }
    temp_storage_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    # Mettre à jour le budget
    budget_repository.update_budget("user_1", "2026-01", 75.0, 100.0)
    
    # Vérifier le contenu mis à jour
    data = json.loads(temp_storage_file.read_text(encoding='utf-8'))
    user_budget = data["budgets"]["user_1"]
    assert user_budget["amount"] == 75.0
    assert user_budget["quota"] == 100.0


def test_reset_month_new_user(budget_repository, temp_storage_file):
    """Teste reset_month pour un nouvel utilisateur."""
    budget_repository.reset_month("user_1", "2026-01")
    
    # Vérifier que le fichier a été créé
    assert temp_storage_file.exists()
    
    # Vérifier le contenu
    data = json.loads(temp_storage_file.read_text(encoding='utf-8'))
    user_budget = data["budgets"]["user_1"]
    assert user_budget["month"] == "2026-01"
    assert user_budget["amount"] == 0.0
    assert user_budget["quota"] == 0.0


def test_reset_month_existing_user_preserve_quota(budget_repository, temp_storage_file):
    """Teste reset_month pour un utilisateur existant (préserve quota)."""
    # Setup: créer un budget existant
    data = {
        "budgets": {
            "user_1": {
                "month": "2025-12",
                "amount": 90.0,
                "quota": 100.0,
                "updated_at": datetime.now().isoformat()
            }
        }
    }
    temp_storage_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    # Reset vers nouveau mois
    budget_repository.reset_month("user_1", "2026-01")
    
    # Vérifier le contenu
    data = json.loads(temp_storage_file.read_text(encoding='utf-8'))
    user_budget = data["budgets"]["user_1"]
    assert user_budget["month"] == "2026-01"
    assert user_budget["amount"] == 0.0  # Reset à 0
    assert user_budget["quota"] == 100.0  # Quota préservé
