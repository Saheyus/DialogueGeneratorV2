"""Tests unitaires pour OpenAIReasoningExtractor."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from core.llm.openai.reasoning_extractor import OpenAIReasoningExtractor


class TestOpenAIReasoningExtractor:
    """Tests pour OpenAIReasoningExtractor."""

    def test_extract_reasoning_from_response_metadata_with_data(self):
        """Test extraction reasoning depuis response.reasoning."""
        mock_response = MagicMock()
        mock_reasoning = MagicMock()
        mock_reasoning.effort = "medium"
        mock_reasoning.summary = "detailed"
        mock_reasoning.items = [MagicMock(), MagicMock()]
        mock_response.reasoning = mock_reasoning
        
        trace = OpenAIReasoningExtractor.extract_reasoning_from_response_metadata(
            mock_response, variant_index=1
        )
        
        assert trace is not None
        assert trace["effort"] == "medium"
        assert trace["summary"] == "detailed"
        assert trace["items_count"] == 2

    def test_extract_reasoning_from_response_metadata_no_reasoning(self):
        """Test extraction quand response.reasoning est absent."""
        mock_response = MagicMock()
        mock_response.reasoning = None
        
        trace = OpenAIReasoningExtractor.extract_reasoning_from_response_metadata(
            mock_response, variant_index=1
        )
        
        assert trace is None

    def test_extract_reasoning_from_output_with_reasoning_item(self):
        """Test extraction reasoning depuis output."""
        mock_item = MagicMock()
        mock_item.type = "reasoning"
        mock_item.summary = "Test summary"
        mock_item.items = [MagicMock(), MagicMock()]
        
        output_items = [mock_item]
        trace = OpenAIReasoningExtractor.extract_reasoning_from_output(
            output_items, existing_trace=None
        )
        
        assert trace is not None
        assert trace["summary"] == "Test summary"
        assert trace["items_count"] == 2

    def test_extract_reasoning_from_output_with_list_summary(self):
        """Test extraction reasoning avec summary comme liste."""
        mock_item = MagicMock()
        mock_item.type = "reasoning"
        mock_item.summary = ["Part 1", "Part 2"]
        mock_item.items = None
        
        output_items = [mock_item]
        trace = OpenAIReasoningExtractor.extract_reasoning_from_output(
            output_items, existing_trace=None
        )
        
        assert trace is not None
        assert trace["summary"] == "Part 1\nPart 2"

    def test_extract_reasoning_from_output_no_reasoning_item(self):
        """Test extraction quand aucun item reasoning dans output."""
        mock_item = MagicMock()
        mock_item.type = "text"
        
        output_items = [mock_item]
        trace = OpenAIReasoningExtractor.extract_reasoning_from_output(
            output_items, existing_trace=None
        )
        
        assert trace is None

    @pytest.mark.asyncio
    async def test_extract_and_notify_reasoning_with_callback(self):
        """Test extraction complète avec callback."""
        mock_response = MagicMock()
        mock_reasoning = MagicMock()
        mock_reasoning.effort = "medium"
        mock_reasoning.summary = "detailed"
        mock_reasoning.items = []
        mock_response.reasoning = mock_reasoning
        mock_response.output = []
        
        callback_called = False
        callback_trace = None
        
        async def mock_callback(trace):
            nonlocal callback_called, callback_trace
            callback_called = True
            callback_trace = trace
        
        trace = await OpenAIReasoningExtractor.extract_and_notify_reasoning(
            mock_response, variant_index=1, reasoning_callback=mock_callback
        )
        
        assert callback_called is True
        assert callback_trace is not None
        assert trace is not None

    @pytest.mark.asyncio
    async def test_extract_and_notify_reasoning_without_callback(self):
        """Test extraction complète sans callback."""
        mock_response = MagicMock()
        mock_response.reasoning = None
        mock_response.output = []
        
        trace = await OpenAIReasoningExtractor.extract_and_notify_reasoning(
            mock_response, variant_index=1, reasoning_callback=None
        )
        
        # Peut être None si pas de reasoning
        assert trace is None or isinstance(trace, dict)
