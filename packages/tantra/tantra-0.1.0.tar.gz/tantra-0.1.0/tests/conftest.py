"""Shared pytest fixtures for Tantra tests."""

from datetime import UTC, datetime
from typing import Any

import pytest

from tantra import Message, ToolSet, tool
from tantra.checkpoints import Checkpoint, CheckpointStore
from tantra.providers.base import ModelProvider
from tantra.types import ProviderResponse, ToolCallData


class MemoryCheckpointStore(CheckpointStore):
    """In-memory checkpoint store for tests."""

    def __init__(self):
        self._checkpoints: dict[str, Checkpoint] = {}

    async def save(self, checkpoint: Checkpoint) -> str:
        """Store checkpoint in memory."""
        self._checkpoints[checkpoint.id] = checkpoint
        return checkpoint.id

    async def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Retrieve checkpoint from memory by ID."""
        return self._checkpoints.get(checkpoint_id)

    async def update(self, checkpoint_id: str, **updates: Any) -> bool:
        """Update checkpoint fields in memory."""
        if checkpoint_id not in self._checkpoints:
            return False

        checkpoint = self._checkpoints[checkpoint_id]
        for key, value in updates.items():
            if hasattr(checkpoint, key):
                setattr(checkpoint, key, value)

        return True

    async def delete(self, checkpoint_id: str) -> bool:
        """Remove checkpoint from memory."""
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    async def list_pending(self, name: str | None = None) -> list[Checkpoint]:
        """List pending checkpoints from memory."""
        pending = [c for c in self._checkpoints.values() if c.status == "pending"]
        if name:
            pending = [c for c in pending if c.name == name]
        return pending

    async def list_by_name(
        self,
        name: str,
        session_id: str | None = None,
        status: str | None = None,
    ) -> list[Checkpoint]:
        """List checkpoints filtered by name and optional criteria."""
        result = [c for c in self._checkpoints.values() if c.name == name]
        if session_id is not None:
            result = [c for c in result if c.session_id == session_id]
        if status is not None:
            result = [c for c in result if c.status == status]
        return sorted(result, key=lambda c: c.created_at)

    async def cleanup_expired(self) -> int:
        """Mark expired checkpoints as expired in memory."""
        now = datetime.now(UTC)
        expired = [
            cid
            for cid, c in self._checkpoints.items()
            if c.expires_at and c.expires_at < now and c.status == "pending"
        ]
        for cid in expired:
            self._checkpoints[cid].status = "expired"
        return len(expired)


class MockProvider(ModelProvider):
    """Mock provider for testing without hitting real APIs."""

    def __init__(
        self,
        responses: list[str | ProviderResponse] | None = None,
        model_name: str = "mock-model",
    ):
        self._responses = responses or ["Hello!"]
        self._call_index = 0
        self._model_name = model_name
        self.calls = []  # Record all calls for assertions

    async def complete(self, messages, tools=None, **kwargs):
        self.calls.append({"messages": messages, "tools": tools, "kwargs": kwargs})

        if self._call_index >= len(self._responses):
            response = self._responses[-1]
        else:
            response = self._responses[self._call_index]

        self._call_index += 1

        if isinstance(response, ProviderResponse):
            return response

        return ProviderResponse(
            content=response,
            tool_calls=None,
            prompt_tokens=10,
            completion_tokens=5,
        )

    def count_tokens(self, messages):
        return sum(len(m.text) for m in messages)

    @property
    def model_name(self):
        return self._model_name

    @property
    def provider_name(self):
        return "mock"

    @property
    def cost_per_1k_input(self):
        return 0.001

    @property
    def cost_per_1k_output(self):
        return 0.002


@pytest.fixture
def mock_provider():
    """Create a mock provider."""
    return MockProvider()


@pytest.fixture
def mock_provider_with_tool_call():
    """Create a mock provider that makes a tool call then responds."""
    tool_call = ToolCallData(
        id="call-123",
        name="get_weather",
        arguments={"city": "Tokyo"},
    )
    return MockProvider(
        responses=[
            ProviderResponse(
                content=None,
                tool_calls=[tool_call],
                prompt_tokens=10,
                completion_tokens=5,
            ),
            ProviderResponse(
                content="The weather in Tokyo is sunny!",
                tool_calls=None,
                prompt_tokens=15,
                completion_tokens=10,
            ),
        ]
    )


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city."""
        return f"Weather in {city}: Sunny, 72F"

    @tool
    def add_numbers(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    return ToolSet([get_weather, add_numbers])


@pytest.fixture
def sample_messages():
    """Create sample messages for testing."""
    return [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there!"),
        Message(role="user", content="How are you?"),
    ]
