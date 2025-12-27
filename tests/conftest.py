"""Configuration globale des tests pytest."""
import os
import pytest
from fastapi.testclient import TestClient

# IMPORTANT: certains singletons (SecurityConfig / rate limiter) sont initialisés à l'import de `api.main`.
# On fixe donc l'env AVANT l'import pour éviter des 429 en tests.
os.environ.setdefault("AUTH_RATE_LIMIT_ENABLED", "false")

from api.main import app


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """Désactive le rate limiting pour tous les tests.
    
    Cette fixture s'exécute automatiquement avant tous les tests pour s'assurer
    que le rate limiting est désactivé, ce qui évite les erreurs 429 pendant les tests.
    """
    # Désactiver le rate limiting via variable d'environnement
    os.environ["AUTH_RATE_LIMIT_ENABLED"] = "false"
    
    yield
    
    # Nettoyer après les tests (optionnel, car les tests ne modifient pas l'environnement global)
    if "AUTH_RATE_LIMIT_ENABLED" in os.environ:
        del os.environ["AUTH_RATE_LIMIT_ENABLED"]


@pytest.fixture
def client():
    """Fixture pour créer un client de test FastAPI.
    
    Returns:
        TestClient: Client de test FastAPI.
    """
    return TestClient(app)



