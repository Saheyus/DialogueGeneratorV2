"""Tests unitaires pour OpenAIStreamParser."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.llm.openai.stream_parser import OpenAIStreamParser, StreamChunk, StreamEventType


class TestOpenAIStreamParser:
    """Tests pour OpenAIStreamParser."""
    
    @pytest.fixture
    def parser(self):
        """Fixture pour créer un parser."""
        return OpenAIStreamParser()
    
    @pytest.fixture
    def parser_with_callback(self):
        """Fixture pour créer un parser avec callback."""
        callback = AsyncMock()
        return OpenAIStreamParser(reasoning_callback=callback)
    
    @pytest.mark.asyncio
    async def test_parse_output_text_delta(self, parser):
        """Test parsing d'un chunk output_text.delta."""
        # Mock d'un événement streaming
        mock_event = MagicMock()
        mock_event.type = "response.output_text.delta"
        mock_event.delta = "Hello"
        mock_event.sequence_number = 1
        
        # Mock du stream
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].event_type == "response.output_text.delta"
        assert chunks[0].data["text"] == "Hello"
        assert chunks[0].sequence == 1
    
    @pytest.mark.asyncio
    async def test_parse_function_call_arguments_delta(self, parser):
        """Test parsing d'un chunk function_call_arguments.delta avec accumulation."""
        # Mock de plusieurs événements pour accumuler les arguments
        mock_event1 = MagicMock()
        mock_event1.type = "response.function_call_arguments.delta"
        mock_event1.item_id = "item_123"
        mock_event1.delta = '{"title": "'
        mock_event1.sequence_number = 1
        
        mock_event2 = MagicMock()
        mock_event2.type = "response.function_call_arguments.delta"
        mock_event2.item_id = "item_123"
        mock_event2.delta = 'Test"}'
        mock_event2.sequence_number = 2
        
        async def mock_stream():
            yield mock_event1
            yield mock_event2
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0].data["delta"] == '{"title": "'
        assert chunks[0].data["accumulated"] == '{"title": "'
        assert chunks[1].data["delta"] == 'Test"}'
        assert chunks[1].data["accumulated"] == '{"title": "Test"}'
        
        # Vérifier que les arguments sont accumulés dans le buffer
        assert parser.get_completed_function_call_arguments("item_123") == '{"title": "Test"}'
    
    @pytest.mark.asyncio
    async def test_parse_function_call_arguments_done(self, parser):
        """Test parsing d'un événement function_call_arguments.done."""
        # Mock d'un événement done avec arguments complets
        mock_event = MagicMock()
        mock_event.type = "response.function_call_arguments.done"
        mock_event.item_id = "item_123"
        mock_event.arguments = '{"title": "Test", "content": "Hello"}'
        mock_event.sequence_number = 1
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].event_type == "response.function_call_arguments.done"
        assert chunks[0].data["arguments"] == '{"title": "Test", "content": "Hello"}'
    
    @pytest.mark.asyncio
    async def test_parse_reasoning_text_delta_with_callback(self, parser_with_callback):
        """Test parsing d'un chunk reasoning_text.delta avec callback."""
        mock_event = MagicMock()
        mock_event.type = "response.reasoning_text.delta"
        mock_event.item_id = "reasoning_123"
        mock_event.delta = "The user wants"
        mock_event.sequence_number = 1
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser_with_callback.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].data["delta"] == "The user wants"
        
        # Vérifier que le callback a été appelé
        parser_with_callback.reasoning_callback.assert_called_once()
        call_args = parser_with_callback.reasoning_callback.call_args[0][0]
        assert call_args["item_id"] == "reasoning_123"
        assert call_args["delta"] == "The user wants"
    
    @pytest.mark.asyncio
    async def test_parse_reasoning_summary_text_delta(self, parser_with_callback):
        """Test parsing d'un chunk reasoning_summary_text.delta."""
        mock_event = MagicMock()
        mock_event.type = "response.reasoning_summary_text.delta"
        mock_event.item_id = "reasoning_123"
        mock_event.delta = "Summary: "
        mock_event.sequence_number = 1
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser_with_callback.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].event_type == "response.reasoning_summary_text.delta"
        assert chunks[0].data["delta"] == "Summary: "
        
        # Vérifier que le callback a été appelé avec type="summary"
        parser_with_callback.reasoning_callback.assert_called_once()
        call_args = parser_with_callback.reasoning_callback.call_args[0][0]
        assert call_args["type"] == "summary"
    
    @pytest.mark.asyncio
    async def test_parse_response_completed(self, parser):
        """Test parsing d'un événement response.completed."""
        mock_response = MagicMock()
        mock_response.id = "resp_123"
        mock_response.status = "completed"
        
        mock_event = MagicMock()
        mock_event.type = "response.completed"
        mock_event.response = mock_response
        mock_event.sequence_number = 1
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].event_type == "response.completed"
        assert parser.get_completed_response() == mock_response
    
    @pytest.mark.asyncio
    async def test_parse_response_failed(self, parser):
        """Test parsing d'un événement response.failed."""
        mock_error = {"code": "server_error", "message": "API error"}
        
        mock_event = MagicMock()
        mock_event.type = "response.failed"
        mock_event.error = mock_error
        mock_event.sequence_number = 1
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert chunks[0].event_type == "response.failed"
        assert chunks[0].data["error"] == mock_error
    
    @pytest.mark.asyncio
    async def test_parse_multiple_events(self, parser):
        """Test parsing de plusieurs événements dans le stream."""
        mock_events = [
            MagicMock(type="response.output_text.delta", delta="Hello", sequence_number=1),
            MagicMock(type="response.output_text.delta", delta=" World", sequence_number=2),
            MagicMock(type="response.completed", response=MagicMock(id="resp_123"), sequence_number=3),
        ]
        
        async def mock_stream():
            for event in mock_events:
                yield event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0].data["text"] == "Hello"
        assert chunks[1].data["text"] == " World"
        assert chunks[2].event_type == "response.completed"
    
    @pytest.mark.asyncio
    async def test_parse_unknown_event(self, parser):
        """Test parsing d'un événement inconnu (doit être ignoré mais loggé)."""
        mock_event = MagicMock()
        mock_event.type = "response.unknown_event"
        mock_event.sequence_number = 1
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        # Les événements inconnus ne sont pas yieldés
        assert len(chunks) == 0
    
    @pytest.mark.asyncio
    async def test_parse_event_without_type(self, parser):
        """Test parsing d'un événement sans type (doit être ignoré)."""
        mock_event = MagicMock()
        del mock_event.type  # Pas de type
        
        async def mock_stream():
            yield mock_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        # Les événements sans type sont ignorés
        assert len(chunks) == 0
    
    @pytest.mark.asyncio
    async def test_get_completed_reasoning_summary(self, parser):
        """Test récupération du reasoning summary accumulé."""
        # Simuler l'accumulation d'un summary
        parser.reasoning_buffer["reasoning_123_summary"] = "This is a summary"
        
        summary = parser.get_completed_reasoning_summary("reasoning_123")
        assert summary == "This is a summary"
        
        # Test avec item_id inexistant
        summary_none = parser.get_completed_reasoning_summary("nonexistent")
        assert summary_none is None
    
    @pytest.mark.asyncio
    async def test_parse_error_handling(self, parser):
        """Test gestion d'erreur lors du parsing."""
        # Mock d'un événement qui lève une exception lors du parsing des données
        # On simule une erreur lors de l'extraction des données (dans le bloc try/except)
        mock_event = MagicMock()
        mock_event.type = "response.output_text.delta"
        # Simuler une erreur lors de l'accès à event_data.get("delta")
        # En faisant en sorte que event_data.get lève une exception
        mock_event.delta = None  # Pas de delta pour déclencher l'erreur dans le parsing
        
        # Créer un mock qui lève une exception lors de l'accès à certaines méthodes
        class ErrorEvent:
            def __init__(self):
                self.type = "response.output_text.delta"
            
            def __getattr__(self, name):
                if name == "delta":
                    raise ValueError("Stream error")
                return None
        
        error_event = ErrorEvent()
        
        async def mock_stream():
            yield error_event
        
        chunks = []
        async for chunk in parser.parse_stream(mock_stream()):
            chunks.append(chunk)
        
        # Une erreur doit générer un chunk d'erreur
        assert len(chunks) == 1
        assert chunks[0].event_type == StreamEventType.ERROR
        assert "error" in chunks[0].data
