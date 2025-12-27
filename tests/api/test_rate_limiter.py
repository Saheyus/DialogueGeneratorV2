"""Tests pour le rate limiting."""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from api.middleware.rate_limiter import (
    get_rate_limiter,
    get_limiter,
    get_rate_limit_string,
    rate_limit_exception_handler
)
from api.config.security_config import get_security_config


def test_get_rate_limiter_enabled():
    """Test que get_rate_limiter retourne un limiter quand activé."""
    with patch.dict(os.environ, {
        "AUTH_RATE_LIMIT_ENABLED": "true",
        "AUTH_RATE_LIMIT_REQUESTS": "5",
        "AUTH_RATE_LIMIT_WINDOW": "60"
    }, clear=True):
        # Réinitialiser la config singleton (elle lit l'env au premier accès)
        import api.config.security_config
        api.config.security_config._security_config = None
        # Réinitialiser le singleton pour le test
        import api.middleware.rate_limiter
        api.middleware.rate_limiter._rate_limiter = None
        
        limiter = get_rate_limiter()
        
        assert limiter is not None
        # Vérifier que c'est une instance de Limiter (ou du type retourné)
        from slowapi import Limiter
        assert isinstance(limiter, Limiter)


def test_get_rate_limiter_disabled():
    """Test que get_rate_limiter retourne None quand désactivé."""
    with patch.dict(os.environ, {"AUTH_RATE_LIMIT_ENABLED": "false"}, clear=True):
        # Réinitialiser la config singleton (elle lit l'env au premier accès)
        import api.config.security_config
        api.config.security_config._security_config = None
        # Réinitialiser le singleton pour le test
        import api.middleware.rate_limiter
        api.middleware.rate_limiter._rate_limiter = None
        
        limiter = get_rate_limiter()
        
        assert limiter is None


def test_get_rate_limit_string():
    """Test que get_rate_limit_string retourne le bon format."""
    with patch.dict(os.environ, {
        "AUTH_RATE_LIMIT_REQUESTS": "5",
        "AUTH_RATE_LIMIT_WINDOW": "60"
    }, clear=True):
        import api.config.security_config
        api.config.security_config._security_config = None
        rate_limit_str = get_rate_limit_string()
        
        assert rate_limit_str == "5/60 seconds"


def test_rate_limit_exception_handler():
    """Test que le handler d'exception de rate limiting fonctionne."""
    # Créer un mock request
    request = MagicMock(spec=Request)
    request.state.request_id = "test-request-id"
    
    # Créer une exception RateLimitExceeded (slowapi attend un objet Limit, pas une string)
    limit = MagicMock()
    limit.error_message = ""
    exc = RateLimitExceeded(limit)
    
    # Appeler le handler
    import asyncio
    response = asyncio.run(rate_limit_exception_handler(request, exc))
    
    # Vérifier la réponse
    assert response.status_code == 429
    data = response.body
    assert b"RATE_LIMIT_EXCEEDED" in data
    assert b"test-request-id" in data


def test_rate_limiter_singleton():
    """Test que get_limiter retourne une instance singleton."""
    with patch.dict(os.environ, {"AUTH_RATE_LIMIT_ENABLED": "true"}, clear=True):
        import api.config.security_config
        api.config.security_config._security_config = None
        # Réinitialiser le singleton pour le test
        import api.middleware.rate_limiter
        api.middleware.rate_limiter._rate_limiter = None
        
        limiter1 = get_limiter()
        limiter2 = get_limiter()
        
        # Doit être la même instance (ou None si désactivé)
        assert limiter1 is limiter2

