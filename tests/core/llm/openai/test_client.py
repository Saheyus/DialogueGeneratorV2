"""Tests unitaires pour OpenAIClient refactorisé."""

import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from pydantic import BaseModel, Field
from core.llm.openai.client import OpenAIClient
from core.llm.llm_client import ILLMClient


class TestClientModel(BaseModel):
    """Modèle de test pour structured output."""
    title: str = Field(description="Titre")
    content: str = Field(description="Contenu")


class TestOpenAIClient:
    """Tests pour OpenAIClient refactorisé."""

    @pytest.fixture
    def mock_api_key(self):
        """Fixture pour mock API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            yield "test-key"

    @pytest.fixture
    def client_config(self):
        """Fixture pour config client."""
        return {
            "default_model": "gpt-5.2",
            "temperature": 0.7,
            "max_tokens": 1500,
        }

    def test_client_implements_illm_client(self, mock_api_key, client_config):
        """Test que OpenAIClient implémente ILLMClient."""
        client = OpenAIClient(api_key=mock_api_key, config=client_config)
        assert isinstance(client, ILLMClient)

    def test_client_initialization(self, mock_api_key, client_config):
        """Test initialisation du client."""
        client = OpenAIClient(api_key=mock_api_key, config=client_config)
        
        assert client.model_name == "gpt-5.2"
        assert client.temperature == 0.7
        assert client.max_tokens == 1500
        assert client.client is not None

    def test_client_initialization_without_api_key(self, client_config):
        """Test initialisation sans API key (doit lever ValueError)."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Clé API OpenAI"):
                OpenAIClient(config=client_config)

    @pytest.mark.asyncio
    async def test_generate_variants_text_mode(self, mock_api_key, client_config):
        """Test génération variantes en mode texte."""
        client = OpenAIClient(api_key=mock_api_key, config=client_config)
        
        # Mock la réponse API
        mock_response = MagicMock()
        mock_item = MagicMock()
        mock_item.type = "text"
        mock_item.text = "Test response"
        mock_response.output = [mock_item]
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5
        mock_response.usage = mock_usage
        mock_response.reasoning = None
        
        with patch.object(client.client.responses, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            results = await client.generate_variants("Test prompt", k=1)
            
            assert len(results) == 1
            assert results[0] == "Test response"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_variants_structured_mode(self, mock_api_key, client_config):
        """Test génération variantes en mode structured output."""
        client = OpenAIClient(api_key=mock_api_key, config=client_config)
        
        # Mock la réponse API
        mock_response = MagicMock()
        mock_item = MagicMock()
        mock_item.type = "function_call"
        mock_item.name = "generate_interaction"
        mock_item.arguments = '{"title": "Test", "content": "Content"}'
        mock_response.output = [mock_item]
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5
        mock_response.usage = mock_usage
        mock_response.reasoning = None
        
        with patch.object(client.client.responses, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            results = await client.generate_variants("Test prompt", k=1, response_model=TestClientModel)
            
            assert len(results) == 1
            assert isinstance(results[0], TestClientModel)
            assert results[0].title == "Test"
            mock_create.assert_called_once()

    def test_get_max_tokens_gpt_5_2(self, mock_api_key, client_config):
        """Test get_max_tokens pour GPT-5.2."""
        client = OpenAIClient(api_key=mock_api_key, config=client_config)
        
        max_tokens = client.get_max_tokens()
        
        assert max_tokens == 128000

    def test_get_max_tokens_unknown_model(self, mock_api_key):
        """Test get_max_tokens pour modèle inconnu."""
        config = {"default_model": "unknown-model"}
        client = OpenAIClient(api_key=mock_api_key, config=config)
        
        max_tokens = client.get_max_tokens()
        
        assert max_tokens == 4096

    @pytest.mark.asyncio
    async def test_close(self, mock_api_key, client_config):
        """Test fermeture du client."""
        client = OpenAIClient(api_key=mock_api_key, config=client_config)
        
        with patch.object(client.client, 'close', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()
