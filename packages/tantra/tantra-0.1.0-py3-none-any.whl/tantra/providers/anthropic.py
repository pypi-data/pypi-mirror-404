"""Anthropic provider implementation for Tantra.

Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Anthropic models.
Uses the official Anthropic Python SDK.

Usage:
    from tantra import Agent
    agent = Agent("anthropic:claude-3-5-sonnet-20241022")
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from ..exceptions import ProviderError
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

# Pricing per 1K tokens (as of early 2026)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-opus-latest": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    # Newer models
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
}


class AnthropicProvider(ModelProvider):
    """Anthropic LLM provider.

    Uses the Anthropic API to generate completions with Claude models.
    Supports tool calling and streaming.

    Examples:
        ```python
        provider = AnthropicProvider("claude-3-5-sonnet-20241022")
        response = await provider.complete([
            Message(role="user", content="Hello!")
        ])
        print(response.content)

        # Or use with Agent
        agent = Agent("anthropic:claude-3-5-sonnet-20241022")
        ```
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **client_kwargs: Any,
    ):
        """Initialize the Anthropic provider.

        Args:
            model: The model to use (e.g., "claude-3-5-sonnet-20241022").
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
            base_url: Optional custom base URL for API requests.
            temperature: Sampling temperature (0-1). Default 0.7.
            max_tokens: Maximum tokens in response. Default 4096.
            **client_kwargs: Additional arguments passed to AsyncAnthropic client.

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

        self._client = AsyncAnthropic(**client_args)

    @property
    def model_name(self) -> str:
        """The model identifier."""
        return self._model

    @property
    def provider_name(self) -> str:
        """The provider name for telemetry."""
        return "anthropic"

    @property
    def cost_per_1k_input(self) -> float:
        """Cost per 1000 input tokens in USD."""
        pricing = MODEL_PRICING.get(self._model, MODEL_PRICING["claude-3-5-sonnet-20241022"])
        return pricing["input"]

    @property
    def cost_per_1k_output(self) -> float:
        """Cost per 1000 output tokens in USD."""
        pricing = MODEL_PRICING.get(self._model, MODEL_PRICING["claude-3-5-sonnet-20241022"])
        return pricing["output"]

    def count_tokens(self, messages: list[Message]) -> int:
        """Estimate token count for messages.

        Anthropic doesn't provide a public tokenizer, so this is an estimate
        based on ~4 characters per token. Images are estimated at ~1600 tokens.

        Args:
            messages: List of messages to count tokens for.

        Returns:
            Approximate token count.
        """
        total = 0
        for msg in messages:
            if msg.content:
                if isinstance(msg.content, str):
                    total += len(msg.content) // 4
                elif isinstance(msg.content, list):
                    for block in msg.content:
                        if isinstance(block, TextContent):
                            total += len(block.text) // 4
                        elif isinstance(block, ImageContent):
                            total += 1600
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += len(tc.name) // 4
                    total += len(json.dumps(tc.arguments)) // 4
        return total + 50  # Buffer for message structure

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Send messages to Anthropic and get a response.

        Args:
            messages: Conversation messages.
            tools: Optional tool schemas (OpenAI format, will be converted).
            **kwargs: Additional Anthropic API parameters.

        Returns:
            ProviderResponse with content and/or tool calls.

        Raises:
            ProviderError: If the API call fails.
        """
        # Convert messages to Anthropic format
        system_prompt, anthropic_messages = self._convert_messages(messages)

        # Build API request
        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self._max_tokens),
            "temperature": kwargs.get("temperature", self._temperature),
        }

        if system_prompt:
            request_kwargs["system"] = system_prompt

        if tools:
            request_kwargs["tools"] = self._convert_tools(tools)

        # Make API call
        try:
            response = await self._client.messages.create(**request_kwargs)
        except Exception as e:
            raise ProviderError(str(e), provider="anthropic")

        # Extract response data
        content = ""
        tool_calls: list[ToolCallData] | None = None

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(
                    ToolCallData(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        return ProviderResponse(
            content=content if content else None,
            tool_calls=tool_calls,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason,
        )

    async def complete_stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream response tokens from Anthropic.

        Args:
            messages: Conversation messages.
            tools: Optional tool schemas.
            **kwargs: Additional API parameters.

        Yields:
            StreamChunk objects with content tokens.

        Raises:
            ProviderError: If the API call fails.
        """
        system_prompt, anthropic_messages = self._convert_messages(messages)

        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self._max_tokens),
            "temperature": kwargs.get("temperature", self._temperature),
        }

        if system_prompt:
            request_kwargs["system"] = system_prompt

        if tools:
            request_kwargs["tools"] = self._convert_tools(tools)

        try:
            async with self._client.messages.stream(**request_kwargs) as stream:
                accumulated_tool_calls: dict[str, dict] = {}
                # Track which content_block index maps to which tool call ID
                block_index_to_id: dict[int, str] = {}

                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(content=event.delta.text)
                        elif hasattr(event.delta, "partial_json"):
                            # Accumulate tool input JSON fragments
                            block_id = block_index_to_id.get(event.index)
                            if block_id and block_id in accumulated_tool_calls:
                                accumulated_tool_calls[block_id]["_json_parts"].append(
                                    event.delta.partial_json
                                )

                    elif event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            accumulated_tool_calls[event.content_block.id] = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "_json_parts": [],
                            }
                            block_index_to_id[event.index] = event.content_block.id

                    elif event.type == "content_block_stop":
                        # Parse accumulated JSON when block finishes
                        block_id = block_index_to_id.get(event.index)
                        if block_id and block_id in accumulated_tool_calls:
                            tc = accumulated_tool_calls[block_id]
                            raw = "".join(tc.pop("_json_parts"))
                            try:
                                tc["arguments"] = json.loads(raw) if raw else {}
                            except json.JSONDecodeError:
                                tc["arguments"] = {}

                    elif event.type == "message_stop":
                        # Build final tool calls
                        final_tool_calls = None
                        if accumulated_tool_calls:
                            final_tool_calls = [
                                ToolCallData(
                                    id=tc["id"],
                                    name=tc["name"],
                                    arguments=tc.get("arguments", {}),
                                )
                                for tc in accumulated_tool_calls.values()
                            ]

                        yield StreamChunk(
                            content="",
                            tool_calls=final_tool_calls,
                            finish_reason="end_turn",
                            is_final=True,
                        )

        except Exception as e:
            raise ProviderError(str(e), provider="anthropic")

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert Tantra messages to Anthropic format.

        Anthropic uses a separate system parameter, not a system message.

        Args:
            messages: List of Tantra Message objects.

        Returns:
            Tuple of (system_prompt, messages_list).
        """
        system_prompt = None
        anthropic_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.text if isinstance(msg.content, list) else msg.content
                continue

            if msg.role == "tool":
                # Tool results in Anthropic format
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.text
                                if isinstance(msg.content, list)
                                else msg.content,
                            }
                        ],
                    }
                )
                continue

            # Handle tool calls in assistant messages
            if msg.role == "assistant" and msg.tool_calls:
                content: list[dict[str, Any]] = []
                if msg.content:
                    content.append({"type": "text", "text": msg.text})
                for tc in msg.tool_calls:
                    content.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )
                anthropic_messages.append(
                    {
                        "role": msg.role,
                        "content": content,
                    }
                )
                continue

            # Regular user/assistant messages
            if isinstance(msg.content, list):
                content_parts: list[dict[str, Any]] = [
                    self._convert_content_block(block) for block in msg.content
                ]
                anthropic_messages.append(
                    {
                        "role": msg.role,
                        "content": content_parts,
                    }
                )
            else:
                anthropic_messages.append(
                    {
                        "role": msg.role,
                        "content": msg.content or "",
                    }
                )

        return system_prompt, anthropic_messages

    @staticmethod
    def _convert_content_block(
        block: TextContent | ImageContent | FileContent,
    ) -> dict[str, Any]:
        """Convert a ContentBlock to Anthropic content block format.

        Args:
            block: A text, image, or file content block.

        Returns:
            Dict in the Anthropic content block format.

        Raises:
            ValueError: If the block type is unsupported (e.g., FileContent).
        """
        if isinstance(block, TextContent):
            return {"type": "text", "text": block.text}
        if isinstance(block, ImageContent):
            if block.url:
                return {
                    "type": "image",
                    "source": {"type": "url", "url": block.url},
                }
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": block.media_type,
                    "data": block.data,
                },
            }
        if isinstance(block, FileContent):
            raise ValueError(
                "FileContent is not yet supported by the Anthropic provider. "
                "Provider-specific file handling will be added in a future release."
            )
        raise ValueError(f"Unknown content block type: {type(block)}")

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-format tools to Anthropic format.

        Args:
            tools: Tool schemas in OpenAI function-calling format.

        Returns:
            Tool schemas in Anthropic tool format.
        """
        anthropic_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append(
                    {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get(
                            "parameters", {"type": "object", "properties": {}}
                        ),
                    }
                )

        return anthropic_tools
