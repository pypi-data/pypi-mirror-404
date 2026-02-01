"""Base provider interface for Tantra.

This module defines the abstract interface that all LLM providers must implement.
Custom providers can be created by subclassing ModelProvider.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ..types import Message, ProviderResponse, StreamChunk

if TYPE_CHECKING:
    from ..resilience import RateLimiter

# Module-level logger for provider operations
_provider_logger = logging.getLogger("tantra.providers")


class ModelProvider(ABC):
    """Abstract base class for LLM providers.

    To create a custom provider, subclass this and implement all abstract methods.

    Examples:
        ```python
        class MyProvider(ModelProvider):
            async def complete(self, messages, tools=None, **kwargs):
                # Call your LLM API
                return ProviderResponse(content="Hello!")

            def count_tokens(self, messages):
                # Count tokens for the messages
                return len(str(messages))

            @property
            def model_name(self):
                return "my-model"

            @property
            def cost_per_1k_input(self):
                return 0.001

            @property
            def cost_per_1k_output(self):
                return 0.002
        ```
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Send messages to the LLM and get a response.

        Args:
            messages: List of conversation messages.
            tools: Optional list of tool schemas in OpenAI format.
            **kwargs: Additional provider-specific options.

        Returns:
            ProviderResponse containing the LLM's response.

        Raises:
            ProviderError: If the LLM API call fails.
        """
        pass

    @abstractmethod
    def count_tokens(self, messages: list[Message]) -> int:
        """Count the number of tokens in the messages.

        Args:
            messages: List of messages to count tokens for.

        Returns:
            Approximate token count.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The name/identifier of the model."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The name of the provider (e.g., 'openai', 'anthropic', 'ollama').

        Used for telemetry and observability to identify the LLM system.
        """
        pass

    @property
    @abstractmethod
    def cost_per_1k_input(self) -> float:
        """Cost in USD per 1000 input tokens."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_output(self) -> float:
        """Cost in USD per 1000 output tokens."""
        pass

    def __init__(self) -> None:
        self._rate_limiter: RateLimiter | None = None

    @property
    def rate_limiter(self) -> RateLimiter | None:
        """The rate limiter for this provider."""
        return self._rate_limiter

    @rate_limiter.setter
    def rate_limiter(self, limiter: RateLimiter | None) -> None:
        """Set the rate limiter for this provider.

        Args:
            limiter: Rate limiter instance, or None to disable rate limiting.
        """
        self._rate_limiter = limiter

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate the cost for a given token usage.

        Args:
            prompt_tokens: Number of input tokens.
            completion_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        input_cost = (prompt_tokens / 1000) * self.cost_per_1k_input
        output_cost = (completion_tokens / 1000) * self.cost_per_1k_output
        return input_cost + output_cost

    async def _acquire_rate_limit(self, estimated_tokens: int = 0) -> None:
        """Acquire rate limit before making request."""
        if self._rate_limiter:
            _provider_logger.debug(
                f"Rate limit acquire: model={self.model_name}, estimated_tokens={estimated_tokens}"
            )
            await self._rate_limiter.acquire(estimated_tokens)
            _provider_logger.debug(f"Rate limit acquired: model={self.model_name}")

    async def _record_rate_limit(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record usage after response."""
        if self._rate_limiter:
            await self._rate_limiter.record_usage(prompt_tokens, completion_tokens)
            _provider_logger.debug(
                f"Rate limit recorded: model={self.model_name}, prompt={prompt_tokens}, completion={completion_tokens}"
            )

    async def complete_stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream response tokens from the LLM.

        Default implementation falls back to non-streaming complete().
        Override in subclasses for true token-by-token streaming.

        Args:
            messages: List of conversation messages.
            tools: Optional list of tool schemas.
            **kwargs: Additional provider-specific options.

        Yields:
            StreamChunk objects containing tokens as they arrive.

        Raises:
            ProviderError: If the LLM API call fails.
        """
        # Default: fall back to non-streaming
        response = await self.complete(messages, tools, **kwargs)
        yield StreamChunk(
            content=response.content or "",
            tool_calls=response.tool_calls,
            finish_reason=response.finish_reason,
            is_final=True,
        )
