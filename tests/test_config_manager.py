"""Tests pour config_manager (wrapper de compatibilité)."""
from __future__ import annotations

import pytest

import config_manager
from services.configuration_service import ConfigurationService


def test_load_llm_config_uses_configuration_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifie que load_llm_config utilise ConfigurationService."""
    expected_config = {"test": True}

    def fake_get_llm_config(self: ConfigurationService) -> dict:
        return expected_config

    monkeypatch.setattr(ConfigurationService, "get_llm_config", fake_get_llm_config)

    with pytest.warns(DeprecationWarning):
        result = config_manager.load_llm_config()

    assert result == expected_config