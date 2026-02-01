"""OpenAI provider implementation for Tantra.

Supports GPT-4o, GPT-4, GPT-3.5-turbo and other OpenAI models.
Uses the official OpenAI Python SDK.

Usage:
    from tantra import Agent
    agent = Agent("openai:gpt-4o")
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import tiktoken
from openai import AsyncOpenAI

from ..exceptions import ProviderError
from ..observability import trace_llm_call, trace_llm_stream
from ..types import (
    FileContent,
    ImageContent,
    Message,
    ProviderResponse,
    StreamChunk,
    TextContent,
    ToolCallData,
)
from .base import ModelProvider

if TYPE_CHECKING:
    from ..resilience import RateLimiter

# Pricing per 1K tokens as of early 2026
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
}

# Token encoding mapping
MODEL_ENCODINGS: dict[str, str] = {
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4-turbo-preview": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5-turbo-16k": "cl100k_base",
}


class OpenAIProvider(ModelProvider):
    """OpenAI LLM provider.

    Uses the OpenAI API to generate completions. Supports tool calling
    and provides accurate token counting via tiktoken.

    Examples:
        ```python
        provider = OpenAIProvider("gpt-4o")
        response = await provider.complete([
            Message(role="user", content="Hello!")
        ])
        print(response.content)
        ```
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        rate_limiter: RateLimiter | None = None,
        **client_kwargs: Any,
    ):
        """Initialize the OpenAI provider.

        Args:
            model: The model to use (e.g., "gpt-4o", "gpt-4", "gpt-3.5-turbo").
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            base_url: Optional custom base URL for API requests.
            temperature: Sampling temperature (0-2). Default 0.7.
            max_tokens: Maximum tokens in response. None for model default.
            rate_limiter: Optional RateLimiter for rate limiting API calls.
            **client_kwargs: Additional arguments passed to AsyncOpenAI client.

        """
        super().__init__()
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

        # Initialize async client
        client_args: dict[str, Any] = {}
        if api_key:
            client_args["api_key"] = api_key
        if base_url:
            client_args["base_url"] = base_url
        client_args.update(client_kwargs)

        self._client = AsyncOpenAI(**client_args)

        # Initialize tokenizer
        encoding_name = MODEL_ENCODINGS.get(model, "cl100k_base")
        try:
            self._encoding = tiktoken.get_encoding(encoding_name)
        except (KeyError, ValueError):
            # Fallback to cl100k_base if encoding not found
            self._encoding = tiktoken.get_encoding("cl100k_base")

        # Set rate limiter
        self._rate_limiter = rate_limiter

    @property
    def model_name(self) -> str:
        """The model identifier."""
        return self._model

    @property
    def provider_name(self) -> str:
        """The provider name for telemetry."""
        return "openai"

    @property
    def cost_per_1k_input(self) -> float:
        """Cost per 1000 input tokens in USD."""
        pricing = MODEL_PRICING.get(self._model, MODEL_PRICING["gpt-4o"])
        return pricing["input"]

    @property
    def cost_per_1k_output(self) -> float:
        """Cost per 1000 output tokens in USD."""
        pricing = MODEL_PRICING.get(self._model, MODEL_PRICING["gpt-4o"])
        return pricing["output"]

    def count_tokens(self, messages: list[Message]) -> int:
        """Count tokens in messages using tiktoken.

        This provides an accurate count for OpenAI models.
        Images are estimated at 85 tokens (low detail) or 765 tokens (high/auto).

        Args:
            messages: List of messages to count tokens for.

        Returns:
            Token count for the given messages.
        """
        total = 0
        for msg in messages:
            # Count role and content
            total += 4  # Every message has overhead tokens
            if msg.content:
                if isinstance(msg.content, str):
                    total += len(self._encoding.encode(msg.content))
                elif isinstance(msg.content, list):
                    for block in msg.content:
                        if isinstance(block, TextContent):
                            total += len(self._encoding.encode(block.text))
                        elif isinstance(block, ImageContent):
                            total += 85 if block.detail == "low" else 765
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += len(self._encoding.encode(tc.name))
                    total += len(self._encoding.encode(json.dumps(tc.arguments)))
        total += 2  # Priming tokens
        return total

    @trace_llm_call
    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Send messages to OpenAI and get a response.

        Args:
            messages: Conversation messages.
            tools: Optional tool schemas.
            **kwargs: Additional OpenAI API parameters.

        Returns:
            ProviderResponse with content and/or tool calls.

        Raises:
            ProviderError: If the API call fails.
        """
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages)

        # Build API request
        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", self._temperature),
        }

        if self._max_tokens:
            request_kwargs["max_tokens"] = self._max_tokens

        if tools:
            request_kwargs["tools"] = tools
            # Allow the model to decide whether to use tools
            request_kwargs["tool_choice"] = kwargs.get("tool_choice", "auto")

        # Rate limiting: acquire before request
        estimated_tokens = self.count_tokens(messages)
        await self._acquire_rate_limit(estimated_tokens)

        # Make API call
        try:
            response = await self._client.chat.completions.create(**request_kwargs)
        except Exception as e:
            # Check for rate limit error
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                import logging

                logging.getLogger("tantra.providers").warning(
                    f"OpenAI rate limit error: model={self._model}, error={e}"
                )
                raise ProviderError(f"Rate limited: {e}", provider="openai")
            raise ProviderError(str(e), provider="openai")

        # Extract response data
        choice = response.choices[0]
        message = choice.message

        # Parse tool calls if present
        tool_calls: list[ToolCallData] | None = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                # Parse arguments from JSON string
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                tool_calls.append(
                    ToolCallData(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        # Record usage for rate limiting
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        await self._record_rate_limit(prompt_tokens, completion_tokens)

        return ProviderResponse(
            content=message.content,
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=choice.finish_reason,
        )

    @trace_llm_stream
    async def complete_stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream response tokens from OpenAI.

        Yields tokens as they arrive for real-time chat UIs.
        Note: Tool calls are accumulated and yielded at the end.

        Args:
            messages: Conversation messages.
            tools: Optional tool schemas.
            **kwargs: Additional OpenAI API parameters.

        Yields:
            StreamChunk objects with content tokens.

        Raises:
            ProviderError: If the API call fails.
        """
        openai_messages = self._convert_messages(messages)

        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", self._temperature),
            "stream": True,
        }

        if self._max_tokens:
            request_kwargs["max_tokens"] = self._max_tokens

        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = kwargs.get("tool_choice", "auto")

        try:
            stream = await self._client.chat.completions.create(**request_kwargs)

            # Accumulate tool calls across chunks
            accumulated_tool_calls: dict[int, dict[str, Any]] = {}
            finish_reason = None

            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                # Yield content tokens
                if delta.content:
                    yield StreamChunk(content=delta.content)

                # Accumulate tool calls (they come in pieces)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.id:
                            accumulated_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                accumulated_tool_calls[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                accumulated_tool_calls[idx]["arguments"] += tc.function.arguments

            # Build final tool calls
            final_tool_calls: list[ToolCallData] | None = None
            if accumulated_tool_calls:
                final_tool_calls = []
                for tc_data in accumulated_tool_calls.values():
                    try:
                        args = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    final_tool_calls.append(
                        ToolCallData(
                            id=tc_data["id"],
                            name=tc_data["name"],
                            arguments=args,
                        )
                    )

            # Yield final chunk with tool calls and finish reason
            yield StreamChunk(
                content="",
                tool_calls=final_tool_calls,
                finish_reason=finish_reason,
                is_final=True,
            )

        except Exception as e:
            raise ProviderError(str(e), provider="openai")

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Tantra messages to OpenAI format.

        Args:
            messages: List of Tantra Message objects.

        Returns:
            List of dicts in the OpenAI chat completions message format.

        Raises:
            ValueError: If a message contains an unsupported content block type.
        """
        openai_messages = []

        for msg in messages:
            openai_msg: dict[str, Any] = {"role": msg.role}

            if msg.content is not None:
                if isinstance(msg.content, str):
                    openai_msg["content"] = msg.content
                elif isinstance(msg.content, list):
                    openai_msg["content"] = [
                        self._convert_content_block(block) for block in msg.content
                    ]

            if msg.tool_call_id is not None:
                openai_msg["tool_call_id"] = msg.tool_call_id

            if msg.tool_calls is not None:
                openai_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]

            openai_messages.append(openai_msg)

        return openai_messages

    @staticmethod
    def _convert_content_block(
        block: TextContent | ImageContent | FileContent,
    ) -> dict[str, Any]:
        """Convert a ContentBlock to an OpenAI content part.

        Args:
            block: A text, image, or file content block.

        Returns:
            Dict in the OpenAI content part format.

        Raises:
            ValueError: If the block type is unsupported (e.g., FileContent).
        """
        if isinstance(block, TextContent):
            return {"type": "text", "text": block.text}
        if isinstance(block, ImageContent):
            if block.url:
                image_url: dict[str, Any] = {"url": block.url}
            else:
                image_url = {"url": f"data:{block.media_type};base64,{block.data}"}
            if block.detail:
                image_url["detail"] = block.detail
            return {"type": "image_url", "image_url": image_url}
        if isinstance(block, FileContent):
            raise ValueError(
                "FileContent is not yet supported by the OpenAI provider. "
                "Provider-specific file handling will be added in a future release."
            )
        raise ValueError(f"Unknown content block type: {type(block)}")


def parse_model_string(model_string: str) -> OpenAIProvider:
    """Parse a model string like 'openai:gpt-4o' into a provider.

    Args:
        model_string: String in format "provider:model" or just "model".

    Returns:
        Configured OpenAIProvider.

    Raises:
        ValueError: If provider is not supported.
    """
    if ":" in model_string:
        provider, model = model_string.split(":", 1)
        if provider.lower() != "openai":
            raise ValueError(
                f"Unsupported provider: {provider}. Only 'openai' is currently supported."
            )
    else:
        model = model_string

    return OpenAIProvider(model=model)
