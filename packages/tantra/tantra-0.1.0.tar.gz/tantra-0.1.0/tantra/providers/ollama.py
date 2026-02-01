"""Ollama provider implementation for Tantra.

Supports local LLM inference with Ollama. Run models like Llama, Mistral,
CodeLlama, and more locally.

Setup:
    # Install Ollama: https://ollama.ai
    ollama pull llama3.2
    ollama pull mistral

Usage:
    from tantra import Agent
    agent = Agent("ollama:llama3.2")
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any

import httpx

from ..exceptions import ProviderError
from ..types import ImageContent, Message, ProviderResponse, StreamChunk, TextContent, ToolCallData
from .base import ModelProvider


class OllamaProvider(ModelProvider):
    """Ollama LLM provider for local inference.

    Uses Ollama's HTTP API to run models locally. Supports tool calling
    for models that support it (e.g., llama3.2, mistral).

    Examples:
        ```python
        provider = OllamaProvider("llama3.2")
        response = await provider.complete([
            Message(role="user", content="Hello!")
        ])
        print(response.content)

        # Or use with Agent
        agent = Agent("ollama:llama3.2")
        agent = Agent("ollama:mistral")
        agent = Agent("ollama:codellama")
        ```
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        num_ctx: int = 4096,
        **options: Any,
    ):
        """Initialize the Ollama provider.

        Args:
            model: The model to use (e.g., "llama3.2", "mistral", "codellama").
            base_url: Ollama API URL. Default is localhost:11434.
            temperature: Sampling temperature (0-1). Default 0.7.
            num_ctx: Context window size. Default 4096.
            **options: Additional Ollama options (top_p, top_k, etc.).

        """
        super().__init__()
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._temperature = temperature
        self._num_ctx = num_ctx
        self._options = options

        # HTTP client for async requests
        self._client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for slow models

    @property
    def model_name(self) -> str:
        """The model identifier."""
        return f"ollama:{self._model}"

    @property
    def provider_name(self) -> str:
        """The provider name for telemetry."""
        return "ollama"

    @property
    def cost_per_1k_input(self) -> float:
        """Cost per 1000 input tokens (free for local models)."""
        return 0.0

    @property
    def cost_per_1k_output(self) -> float:
        """Cost per 1000 output tokens (free for local models)."""
        return 0.0

    def count_tokens(self, messages: list[Message]) -> int:
        """Estimate token count for messages.

        This is a rough estimate based on ~4 characters per token.
        Images are estimated at ~768 tokens.

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
                            total += 768
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += len(tc.name) // 4
                    total += len(json.dumps(tc.arguments)) // 4
        return total + 50

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Send messages to Ollama and get a response.

        Args:
            messages: Conversation messages.
            tools: Optional tool schemas (OpenAI format).
            **kwargs: Additional options.

        Returns:
            ProviderResponse with content and/or tool calls.

        Raises:
            ProviderError: If the API call fails.
        """

        # Convert messages to Ollama format
        ollama_messages = self._convert_messages(messages)

        # Build request
        request_data: dict[str, Any] = {
            "model": self._model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self._temperature),
                "num_ctx": kwargs.get("num_ctx", self._num_ctx),
                **self._options,
            },
        }

        if tools:
            request_data["tools"] = self._convert_tools(tools)

        # Make API call
        try:
            response = await self._client.post(
                f"{self._base_url}/api/chat",
                json=request_data,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError:
            raise ProviderError(
                f"Could not connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running: ollama serve",
                provider="ollama",
            )
        except httpx.HTTPStatusError as e:
            raise ProviderError(str(e), provider="ollama")
        except (httpx.HTTPError, OSError, ValueError) as e:
            raise ProviderError(str(e), provider="ollama")

        # Extract response
        message = data.get("message", {})
        content = message.get("content", "")

        # Parse tool calls if present
        tool_calls: list[ToolCallData] | None = None
        if message.get("tool_calls"):
            tool_calls = []
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                tool_calls.append(
                    ToolCallData(
                        id=tc.get("id", f"call_{len(tool_calls)}"),
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {}),
                    )
                )

        # Estimate tokens (Ollama doesn't always return this)
        prompt_tokens = data.get("prompt_eval_count", self.count_tokens(messages))
        completion_tokens = data.get("eval_count", len(content) // 4)

        return ProviderResponse(
            content=content if content else None,
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop",
        )

    async def complete_stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream response tokens from Ollama.

        Args:
            messages: Conversation messages.
            tools: Optional tool schemas.
            **kwargs: Additional options.

        Yields:
            StreamChunk objects with content tokens.

        Raises:
            ProviderError: If the API call fails.
        """

        ollama_messages = self._convert_messages(messages)

        request_data: dict[str, Any] = {
            "model": self._model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self._temperature),
                "num_ctx": kwargs.get("num_ctx", self._num_ctx),
                **self._options,
            },
        }

        if tools:
            request_data["tools"] = self._convert_tools(tools)

        try:
            async with self._client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=request_data,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = data.get("message", {})
                    content = message.get("content", "")

                    if content:
                        yield StreamChunk(content=content)

                    if data.get("done"):
                        # Parse tool calls from final message
                        tool_calls = None
                        if message.get("tool_calls"):
                            tool_calls = []
                            for tc in message["tool_calls"]:
                                func = tc.get("function", {})
                                tool_calls.append(
                                    ToolCallData(
                                        id=tc.get("id", f"call_{len(tool_calls)}"),
                                        name=func.get("name", ""),
                                        arguments=func.get("arguments", {}),
                                    )
                                )

                        yield StreamChunk(
                            content="",
                            tool_calls=tool_calls,
                            finish_reason="stop",
                            is_final=True,
                        )

        except httpx.ConnectError:
            raise ProviderError(
                f"Could not connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running: ollama serve",
                provider="ollama",
            )
        except (httpx.HTTPError, OSError, ValueError) as e:
            raise ProviderError(str(e), provider="ollama")

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Tantra messages to Ollama format.

        Ollama uses a separate ``images`` field for vision models rather
        than inline content blocks.  Only base64-encoded images are
        supported (Ollama does not accept image URLs natively).

        Args:
            messages: List of Tantra Message objects.

        Returns:
            List of dicts in the Ollama chat message format.
        """
        ollama_messages = []

        for msg in messages:
            if isinstance(msg.content, list):
                # Extract text and images separately for Ollama's format
                text_parts: list[str] = []
                images: list[str] = []
                for block in msg.content:
                    if isinstance(block, TextContent):
                        text_parts.append(block.text)
                    elif isinstance(block, ImageContent) and block.data:
                        images.append(block.data)
                ollama_msg: dict[str, Any] = {
                    "role": msg.role,
                    "content": "".join(text_parts),
                }
                if images:
                    ollama_msg["images"] = images
            else:
                ollama_msg = {
                    "role": msg.role,
                    "content": msg.content or "",
                }

            # Handle tool calls
            if msg.tool_calls:
                ollama_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            # Handle tool results
            if msg.role == "tool":
                ollama_msg["role"] = "tool"
                ollama_msg["tool_call_id"] = msg.tool_call_id

            ollama_messages.append(ollama_msg)

        return ollama_messages

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-format tools to Ollama format.

        Ollama uses the same format as OpenAI for tools.

        Args:
            tools: Tool schemas in OpenAI function-calling format.

        Returns:
            Tool schemas passed through (Ollama uses the same format).
        """
        return tools

    async def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of model names.

        Raises:
            ProviderError: If the request to Ollama fails.
        """

        try:
            response = await self._client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except (httpx.HTTPError, OSError, ValueError) as e:
            raise ProviderError(f"Failed to list models: {e}", provider="ollama")

    async def pull_model(self, model: str) -> None:
        """Pull a model from Ollama library.

        Args:
            model: Model name to pull (e.g., "llama3.2", "mistral").

        Raises:
            ProviderError: If the pull request to Ollama fails.
        """

        try:
            response = await self._client.post(
                f"{self._base_url}/api/pull",
                json={"name": model},
                timeout=600.0,  # 10 min for large models
            )
            response.raise_for_status()
        except (httpx.HTTPError, OSError) as e:
            raise ProviderError(f"Failed to pull model: {e}", provider="ollama")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> OllamaProvider:
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager and close the HTTP client."""
        await self.close()
