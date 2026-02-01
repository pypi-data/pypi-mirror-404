"""Tests for In-the-Loop (ITL) functionality."""

from uuid import uuid4

import pytest

from tantra import (
    AgentRegistry,
    Interrupt,
    InterruptHandler,
    InterruptResponse,
    tool,
)
from tantra.checkpoints import Checkpoint
from tantra.types import Message


class TestToolInterrupt:
    """Tests for the @tool interrupt parameter."""

    def test_tool_with_interrupt(self):
        """Tool with interrupt parameter sets requires_interrupt."""

        @tool(interrupt="Approve this?")
        def my_tool() -> str:
            return "done"

        assert my_tool.requires_interrupt is True
        assert my_tool.interrupt == "Approve this?"

    def test_tool_without_interrupt(self):
        """Tool without interrupt has requires_interrupt=False."""

        @tool
        def my_tool() -> str:
            return "done"

        assert my_tool.requires_interrupt is False
        assert my_tool.interrupt is None


class TestInterruptModels:
    """Tests for Interrupt and InterruptResponse models."""

    def test_interrupt_creation(self):
        """Can create an Interrupt with all fields."""
        interrupt = Interrupt(
            id="int-123",
            run_id=uuid4(),
            name="test-agent",
            prompt="Approve this action?",
            tool_name="delete_user",
            tool_args={"user_id": 123},
            context={"extra": "info"},
        )

        assert interrupt.id == "int-123"
        assert interrupt.prompt == "Approve this action?"
        assert interrupt.tool_name == "delete_user"
        assert interrupt.tool_args == {"user_id": 123}

    def test_interrupt_response_approve(self):
        """InterruptResponse for approval."""
        response = InterruptResponse(value=True, proceed=True)
        assert response.proceed is True
        assert response.value is True

    def test_interrupt_response_reject(self):
        """InterruptResponse for rejection."""
        response = InterruptResponse(proceed=False, reason="Too risky")
        assert response.proceed is False
        assert response.reason == "Too risky"


class TestInterruptHandler:
    """Tests for InterruptHandler implementations."""

    @pytest.mark.asyncio
    async def test_custom_handler(self):
        """Custom handler receives interrupt via notify()."""

        class TestHandler(InterruptHandler):
            def __init__(self):
                self.received = None

            async def notify(self, interrupt: Interrupt) -> None:
                self.received = interrupt

        handler = TestHandler()
        interrupt = Interrupt(
            id="int-123",
            run_id=uuid4(),
            prompt="Test prompt",
        )

        await handler.notify(interrupt)

        assert handler.received == interrupt


class TestCheckpoint:
    """Tests for Checkpoint model."""

    def test_checkpoint_creation(self):
        """Can create a checkpoint with messages."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]

        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test-agent",
            messages=messages,
            pending_tool="my_tool",
            pending_args={"arg": "value"},
            prompt="Approve?",
        )

        assert checkpoint.status == "pending"
        assert len(checkpoint.messages) == 2
        assert checkpoint.pending_tool == "my_tool"


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_register_and_get(self):
        """Can register and retrieve agents."""
        registry = AgentRegistry()

        # Create a mock agent-like object
        class MockAgent:
            _name = None

        agent = MockAgent()
        registry.register("my-agent", agent)

        retrieved = registry.get("my-agent")
        assert retrieved is agent
        assert agent._name == "my-agent"

    def test_unregister(self):
        """Can unregister agents."""
        registry = AgentRegistry()

        class MockAgent:
            _name = None

        agent = MockAgent()
        registry.register("my-agent", agent)

        removed = registry.unregister("my-agent")
        assert removed is True

        retrieved = registry.get("my-agent")
        assert retrieved is None

    def test_list_agents(self):
        """Can list all registered agents."""
        registry = AgentRegistry()

        class MockAgent:
            _name = None

        for i in range(3):
            registry.register(f"agent-{i}", MockAgent())

        agents = registry.list_agents()
        assert len(agents) == 3
        assert "agent-0" in agents
        assert "agent-1" in agents
        assert "agent-2" in agents

    def test_clear(self):
        """Can clear all agents."""
        registry = AgentRegistry()

        class MockAgent:
            _name = None

        registry.register("agent-1", MockAgent())
        registry.register("agent-2", MockAgent())

        registry.clear()
        assert registry.list_agents() == []
