"""Tests for LLM providers."""

import pytest

from tantra.providers import (
    AnthropicProvider,
    ModelProvider,
    OllamaProvider,
    OpenAIProvider,
    parse_model_string,
)
from tantra.types import Message


# Set dummy API keys for testing (providers won't actually be called)
@pytest.fixture(autouse=True)
def mock_api_keys(monkeypatch):
    """Set dummy API keys for provider instantiation."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")


class TestParseModelString:
    """Tests for parse_model_string function."""

    def test_openai_with_prefix(self):
        """Parse openai:model format."""
        provider = parse_model_string("openai:gpt-4o")
        assert isinstance(provider, OpenAIProvider)
        assert provider.model_name == "gpt-4o"

    def test_openai_without_prefix(self):
        """Default to OpenAI when no prefix."""
        provider = parse_model_string("gpt-4o")
        assert isinstance(provider, OpenAIProvider)
        assert provider.model_name == "gpt-4o"

    def test_ollama_provider(self):
        """Parse ollama:model format."""
        provider = parse_model_string("ollama:llama3.2")
        assert isinstance(provider, OllamaProvider)
        assert provider.model_name == "ollama:llama3.2"

    def test_ollama_with_tag(self):
        """Ollama model with tag."""
        provider = parse_model_string("ollama:llama3.2:latest")
        assert isinstance(provider, OllamaProvider)

    def test_anthropic_provider(self):
        """Parse anthropic:model format."""
        provider = parse_model_string("anthropic:claude-3-5-sonnet-20241022")
        assert isinstance(provider, AnthropicProvider)

    def test_unsupported_provider(self):
        """Error on unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            parse_model_string("unknown:model")


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_create_provider(self):
        """Create OpenAI provider."""
        provider = OpenAIProvider("gpt-4o")
        assert provider.model_name == "gpt-4o"

    def test_model_pricing(self):
        """Check pricing is set."""
        provider = OpenAIProvider("gpt-4o")
        assert provider.cost_per_1k_input > 0
        assert provider.cost_per_1k_output > 0

    def test_token_counting(self):
        """Token counting works."""
        provider = OpenAIProvider("gpt-4o")
        messages = [Message(role="user", content="Hello world")]
        tokens = provider.count_tokens(messages)
        assert tokens > 0

    def test_estimate_cost(self):
        """Cost estimation works."""
        provider = OpenAIProvider("gpt-4o")
        cost = provider.estimate_cost(1000, 500)
        assert cost > 0


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    def test_create_provider(self):
        """Create Ollama provider."""
        provider = OllamaProvider("llama3.2")
        assert provider.model_name == "ollama:llama3.2"

    def test_custom_base_url(self):
        """Custom base URL."""
        provider = OllamaProvider("llama3.2", base_url="http://custom:11434")
        assert provider._base_url == "http://custom:11434"

    def test_free_pricing(self):
        """Local models are free."""
        provider = OllamaProvider("llama3.2")
        assert provider.cost_per_1k_input == 0.0
        assert provider.cost_per_1k_output == 0.0

    def test_token_counting(self):
        """Token counting estimate."""
        provider = OllamaProvider("llama3.2")
        messages = [Message(role="user", content="Hello world")]
        tokens = provider.count_tokens(messages)
        assert tokens > 0


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_create_provider(self):
        """Create Anthropic provider."""
        provider = AnthropicProvider("claude-3-5-sonnet-20241022")
        assert provider.model_name == "claude-3-5-sonnet-20241022"

    def test_model_pricing(self):
        """Check pricing is set."""
        provider = AnthropicProvider("claude-3-5-sonnet-20241022")
        assert provider.cost_per_1k_input > 0
        assert provider.cost_per_1k_output > 0

    def test_token_counting(self):
        """Token counting estimate."""
        provider = AnthropicProvider("claude-3-5-sonnet-20241022")
        messages = [Message(role="user", content="Hello world")]
        tokens = provider.count_tokens(messages)
        assert tokens > 0


class TestModelProvider:
    """Tests for ModelProvider base class."""

    def test_is_abstract(self):
        """Cannot instantiate directly."""
        with pytest.raises(TypeError):
            ModelProvider()

    def test_estimate_cost(self):
        """Estimate cost method works on subclass."""
        provider = OpenAIProvider("gpt-4o")
        cost = provider.estimate_cost(prompt_tokens=1000, completion_tokens=500)
        expected = (1000 / 1000) * provider.cost_per_1k_input + (
            500 / 1000
        ) * provider.cost_per_1k_output
        assert cost == pytest.approx(expected)
