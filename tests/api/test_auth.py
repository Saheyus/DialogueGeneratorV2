"""Tests pour l'authentification API."""
import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    """Test de connexion réussie."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client: TestClient):
    """Test de connexion échouée."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_get_current_user_without_auth(client: TestClient):
    """Test d'accès à /me sans authentification."""
    response = client.get("/api/v1/auth/me")
    # En développement, l'auth est désactivée (retourne 200 avec user mock)
    # En production, retourne 401
    from api.config.security_config import get_security_config
    security_config = get_security_config()
    if security_config.is_development:
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"  # User mock
    else:
        assert response.status_code == 401  # HTTPBearer retourne 401 si pas de token


def test_get_current_user_with_auth(client: TestClient):
    """Test d'accès à /me avec authentification."""
    # D'abord se connecter
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Ensuite accéder à /me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == "admin"

