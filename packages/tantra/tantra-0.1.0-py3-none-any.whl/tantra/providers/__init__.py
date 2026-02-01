# Provider implementations
"""
Tantra supports multiple LLM providers through an extensible plugin architecture.

Built-in providers:
    - OpenAI: GPT-4o, GPT-4, GPT-3.5
    - Anthropic: Claude 3.5, Claude 3
    - Ollama: Local models (Llama, Mistral, etc.)

Usage:
    # Using provider string (recommended)
    agent = Agent("openai:gpt-4o")
    agent = Agent("anthropic:claude-3-5-sonnet-20241022")
    agent = Agent("ollama:llama3.2")

    # Using provider instance
    provider = OpenAIProvider("gpt-4o")
    agent = Agent(provider)
"""

from .anthropic import AnthropicProvider
from .base import ModelProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


def parse_model_string(model_string: str) -> ModelProvider:
    """Parse a model string into a provider instance.

    Supports formats:
        - "provider:model" (e.g., "openai:gpt-4o", "anthropic:claude-3-5-sonnet-20241022")
        - "model" (defaults to OpenAI, e.g., "gpt-4o")

    Args:
        model_string: String in format "provider:model" or just "model".

    Returns:
        Configured ModelProvider instance.

    Raises:
        ValueError: If provider is not supported or not installed.

    Examples:
        >>> parse_model_string("openai:gpt-4o")
        OpenAIProvider(model='gpt-4o')

        >>> parse_model_string("anthropic:claude-3-5-sonnet-20241022")
        AnthropicProvider(model='claude-3-5-sonnet-20241022')

        >>> parse_model_string("ollama:llama3.2")
        OllamaProvider(model='llama3.2')

        >>> parse_model_string("gpt-4o")  # Defaults to OpenAI
        OpenAIProvider(model='gpt-4o')
    """
    if ":" in model_string:
        provider, model = model_string.split(":", 1)
        provider = provider.lower()
    else:
        # Default to OpenAI
        provider = "openai"
        model = model_string

    if provider == "openai":
        return OpenAIProvider(model=model)

    elif provider == "anthropic":
        return AnthropicProvider(model=model)

    elif provider == "ollama":
        return OllamaProvider(model=model)

    else:
        raise ValueError(f"Unsupported provider: {provider}. Supported: openai, anthropic, ollama")


__all__ = [
    "AnthropicProvider",
    "ModelProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "parse_model_string",
]
