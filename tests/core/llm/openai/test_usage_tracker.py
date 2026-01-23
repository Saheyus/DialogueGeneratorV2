"""Tests unitaires pour OpenAIUsageTracker."""

import pytest
from unittest.mock import MagicMock
from core.llm.openai.usage_tracker import OpenAIUsageTracker


class TestOpenAIUsageTracker:
    """Tests pour OpenAIUsageTracker."""

    def test_extract_usage_metrics_responses_api(self):
        """Test extraction métriques depuis Responses API."""
        # Mock response avec usage Responses API
        mock_response = MagicMock()
        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_response.usage = mock_usage
        
        metrics = OpenAIUsageTracker.extract_usage_metrics(mock_response)
        
        assert metrics["prompt_tokens"] == 100
        assert metrics["completion_tokens"] == 50
        assert metrics["total_tokens"] == 150

    def test_extract_usage_metrics_chat_completions(self):
        """Test extraction métriques depuis Chat Completions (legacy)."""
        # Mock response avec usage Chat Completions
        mock_response = MagicMock()
        mock_usage = MagicMock()
        # Ne pas définir input_tokens pour forcer le chemin Chat Completions
        del mock_usage.input_tokens
        mock_usage.prompt_tokens = 200
        mock_usage.completion_tokens = 75
        mock_usage.total_tokens = 275
        mock_response.usage = mock_usage
        
        metrics = OpenAIUsageTracker.extract_usage_metrics(mock_response)
        
        assert metrics["prompt_tokens"] == 200
        assert metrics["completion_tokens"] == 75
        assert metrics["total_tokens"] == 275

    def test_extract_usage_metrics_no_usage(self):
        """Test extraction métriques quand usage est absent."""
        mock_response = MagicMock()
        mock_response.usage = None
        
        metrics = OpenAIUsageTracker.extract_usage_metrics(mock_response)
        
        assert metrics["prompt_tokens"] == 0
        assert metrics["completion_tokens"] == 0
        assert metrics["total_tokens"] == 0

    def test_extract_usage_metrics_zero_values(self):
        """Test extraction métriques avec valeurs à zéro."""
        mock_response = MagicMock()
        mock_usage = MagicMock()
        mock_usage.input_tokens = 0
        mock_usage.output_tokens = 0
        mock_response.usage = mock_usage
        
        metrics = OpenAIUsageTracker.extract_usage_metrics(mock_response)
        
        assert metrics["prompt_tokens"] == 0
        assert metrics["completion_tokens"] == 0
        assert metrics["total_tokens"] == 0
