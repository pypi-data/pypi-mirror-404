"""Tests for LLM clients."""

import pytest
from unittest.mock import patch, MagicMock
from rotalabs_verity.llm import (
    LLMResponse,
    LLMClient,
    OpenAIClient,
    AnthropicClient,
    OllamaClient,
    get_client,
)


class TestLLMResponse:
    def test_response_fields(self):
        """LLMResponse should have all required fields."""
        response = LLMResponse(
            content="test code",
            model="gpt-4",
            tokens_used=100,
            latency_ms=500.0
        )

        assert response.content == "test code"
        assert response.model == "gpt-4"
        assert response.tokens_used == 100
        assert response.latency_ms == 500.0


class TestOpenAIClient:
    def test_requires_api_key(self):
        """OpenAI client requires API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                OpenAIClient()

    @patch("openai.OpenAI")
    def test_generate_format(self, mock_openai_class):
        """OpenAI client returns correct response format."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "def test(): pass"
        mock_response.usage.total_tokens = 50
        mock_client.chat.completions.create.return_value = mock_response

        # Create client with explicit API key
        client = OpenAIClient(api_key="test-key")
        response = client.generate("Write a function")

        assert isinstance(response, LLMResponse)
        assert response.content == "def test(): pass"
        assert response.model == "gpt-4"
        assert response.tokens_used == 50
        assert response.latency_ms >= 0


class TestAnthropicClient:
    def test_requires_api_key(self):
        """Anthropic client requires API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                AnthropicClient()

    @patch("anthropic.Anthropic")
    def test_generate_format(self, mock_anthropic_class):
        """Anthropic client returns correct response format."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "def test(): pass"
        mock_response.usage.input_tokens = 30
        mock_response.usage.output_tokens = 20
        mock_client.messages.create.return_value = mock_response

        # Create client with explicit API key
        client = AnthropicClient(api_key="test-key")
        response = client.generate("Write a function")

        assert isinstance(response, LLMResponse)
        assert response.content == "def test(): pass"
        assert response.model == "claude-sonnet-4-20250514"
        assert response.tokens_used == 50
        assert response.latency_ms >= 0


class TestOllamaClient:
    @patch("requests.post")
    def test_generate_format(self, mock_post):
        """Ollama client returns correct response format."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "def test(): pass",
            "eval_count": 25
        }
        mock_post.return_value = mock_response

        client = OllamaClient()
        response = client.generate("Write a function")

        assert isinstance(response, LLMResponse)
        assert response.content == "def test(): pass"
        assert response.model == "codellama:13b"
        assert response.tokens_used == 25
        assert response.latency_ms >= 0

    def test_custom_url(self):
        """Ollama client accepts custom base URL."""
        client = OllamaClient(base_url="http://custom:8080")
        assert client.base_url == "http://custom:8080"


class TestGetClientFactory:
    @patch("openai.OpenAI")
    def test_get_openai_client(self, mock_openai):
        """Factory returns OpenAI client."""
        client = get_client("openai", model="gpt-4")
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4"

    @patch("anthropic.Anthropic")
    def test_get_anthropic_client(self, mock_anthropic):
        """Factory returns Anthropic client."""
        client = get_client("anthropic", model="claude-3-opus-20240229")
        assert isinstance(client, AnthropicClient)
        assert client.model == "claude-3-opus-20240229"

    def test_get_ollama_client(self):
        """Factory returns Ollama client."""
        client = get_client("ollama", model="llama2")
        assert isinstance(client, OllamaClient)
        assert client.model == "llama2"

    def test_unknown_provider(self):
        """Factory raises for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_client("unknown")
