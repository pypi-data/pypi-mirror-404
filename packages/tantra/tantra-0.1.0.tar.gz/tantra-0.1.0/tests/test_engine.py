"""Tests for ExecutionEngine internals.

Tests cover: resume, parallel tool execution,
warden review path, unified interrupt path (notify + checkpoint + raise).
"""

from uuid import uuid4

import pytest
from conftest import MemoryCheckpointStore, MockProvider

from tantra import Message, ToolSet, tool
from tantra.checkpoints import Checkpoint
from tantra.engine import AbortedError, ExecutionEngine, ExecutionInterruptedError
from tantra.intheloop import (
    Interrupt,
    InterruptHandler,
    InterruptResponse,
    Warden,
)
from tantra.intheloop.warden import WardenPreview, warden_tool
from tantra.types import ProviderResponse, ToolCallData

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class MockInterruptHandler(InterruptHandler):
    """Handler that records notify() calls."""

    def __init__(self):
        self.received = []

    async def notify(self, interrupt: Interrupt) -> None:
        self.received.append(interrupt)


def _make_engine(responses=None, tools=None, system_prompt="", **kwargs):
    """Create an ExecutionEngine with MockProvider."""
    provider = MockProvider(responses=responses or ["Hello!"])
    return ExecutionEngine(
        provider=provider,
        tools=tools,
        system_prompt=system_prompt,
        **kwargs,
    )


def _simple_tools():
    """ToolSet with a get_weather tool."""

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city."""
        return f"Sunny in {city}"

    return ToolSet([get_weather])


def _interrupt_tools():
    """ToolSet with a tool that requires interrupt."""

    @tool(interrupt="Approve this deletion?")
    def delete_record(record_id: str) -> str:
        """Delete a record."""
        return f"Deleted {record_id}"

    return ToolSet([delete_record])


def _warden_tools():
    """ToolSet with a warden tool."""

    @warden_tool
    def dangerous_action(target: str) -> str:
        """Do something dangerous."""
        return f"Executed on {target}"

    @dangerous_action.preview
    def preview_dangerous(target: str) -> WardenPreview:
        return WardenPreview(
            tool_name="dangerous_action",
            arguments={"target": target},
            preview_result=f"Will act on {target}",
            description="Dangerous action",
            risks=["May cause damage"],
            reversible=False,
        )

    return ToolSet([dangerous_action])


def _reversible_warden_tools():
    """ToolSet with a reversible warden tool (auto-approvable)."""

    @warden_tool
    def safe_action(target: str) -> str:
        """Do something safe and reversible."""
        return f"Executed safely on {target}"

    @safe_action.preview
    def preview_safe(target: str) -> WardenPreview:
        return WardenPreview(
            tool_name="safe_action",
            arguments={"target": target},
            preview_result=f"Will safely act on {target}",
            description="Safe reversible action",
            risks=[],
            reversible=True,
        )

    return ToolSet([safe_action])


def _tool_call_response(tool_name, arguments, call_id="call-1"):
    """Create a ProviderResponse that calls a tool."""
    return ProviderResponse(
        content=None,
        tool_calls=[ToolCallData(id=call_id, name=tool_name, arguments=arguments)],
        prompt_tokens=10,
        completion_tokens=5,
    )


def _text_response(text):
    """Create a ProviderResponse with text content."""
    return ProviderResponse(
        content=text,
        tool_calls=None,
        prompt_tokens=10,
        completion_tokens=5,
    )


# =========================================================================
# TestEngineResume
# =========================================================================


class TestEngineResume:
    """Checkpoint-based resume after interrupt."""

    @pytest.mark.asyncio
    async def test_resume_approved(self):
        """Resume with approval executes pending tool and continues."""
        tools = _simple_tools()
        store = MemoryCheckpointStore()

        # Create a checkpoint with a pending tool call
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[
                Message(role="user", content="What's the weather?"),
            ],
            pending_tool="get_weather",
            pending_args={"city": "Tokyo"},
            pending_tool_call_id="call-1",
            prompt="Approve weather check?",
            status="pending",
        )
        await store.save(checkpoint)

        engine = _make_engine(
            responses=["The weather is sunny in Tokyo!"],
            tools=tools,
            checkpoint_store=store,
        )

        response = InterruptResponse(value=True, proceed=True)
        result = await engine.resume(checkpoint.id, response)

        assert "sunny" in result.output.lower() or "Tokyo" in result.output

    @pytest.mark.asyncio
    async def test_resume_rejected_raises_aborted(self):
        """Resume with rejection raises AbortedError."""
        tools = _simple_tools()
        store = MemoryCheckpointStore()

        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[Message(role="user", content="Check weather")],
            pending_tool="get_weather",
            pending_args={"city": "Tokyo"},
            pending_tool_call_id="call-1",
            prompt="Approve?",
            status="pending",
        )
        await store.save(checkpoint)

        engine = _make_engine(tools=tools, checkpoint_store=store)

        response = InterruptResponse(value=False, proceed=False, reason="Not now")
        with pytest.raises(AbortedError, match="Not now"):
            await engine.resume(checkpoint.id, response)

    @pytest.mark.asyncio
    async def test_resume_invalid_checkpoint(self):
        """Resume with unknown checkpoint raises ValueError."""
        store = MemoryCheckpointStore()
        engine = _make_engine(checkpoint_store=store)
        response = InterruptResponse(value=True, proceed=True)
        with pytest.raises(ValueError, match="not found"):
            await engine.resume("nonexistent-id", response)

    @pytest.mark.asyncio
    async def test_resume_non_pending_checkpoint(self):
        """Resume with non-pending checkpoint raises ValueError."""
        store = MemoryCheckpointStore()
        checkpoint = Checkpoint(
            run_id=uuid4(),
            name="test",
            messages=[],
            pending_tool="get_weather",
            pending_args={},
            prompt="Approve?",
            status="completed",
        )
        await store.save(checkpoint)

        engine = _make_engine(checkpoint_store=store)
        response = InterruptResponse(value=True, proceed=True)
        with pytest.raises(ValueError, match="not pending"):
            await engine.resume(checkpoint.id, response)


# =========================================================================
# TestEngineParallelTools
# =========================================================================


class TestEngineParallelTools:
    """Parallel tool execution via _execute_tools_parallel."""

    @pytest.mark.asyncio
    async def test_multiple_tools_parallel(self):
        """Multiple tools execute and results are added to memory in order."""

        @tool
        def tool_a(x: str) -> str:
            """Tool A."""
            return f"A:{x}"

        @tool
        def tool_b(x: str) -> str:
            """Tool B."""
            return f"B:{x}"

        tools = ToolSet([tool_a, tool_b])
        engine = _make_engine(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[
                        ToolCallData(id="c1", name="tool_a", arguments={"x": "1"}),
                        ToolCallData(id="c2", name="tool_b", arguments={"x": "2"}),
                    ],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                _text_response("Both done"),
            ],
            tools=tools,
            parallel_tool_execution=True,
        )

        result = await engine.run("run both")

        assert result.output == "Both done"
        # Memory should have tool results
        messages = engine.memory.get_messages()
        tool_msgs = [m for m in messages if m.role == "tool"]
        assert len(tool_msgs) == 2
        assert "A:1" in tool_msgs[0].content
        assert "B:2" in tool_msgs[1].content

    @pytest.mark.asyncio
    async def test_parallel_tool_error_captured(self):
        """Tool error is captured as string, not raised."""

        @tool
        def good_tool(x: str) -> str:
            """Works fine."""
            return f"ok:{x}"

        @tool
        def bad_tool(x: str) -> str:
            """Always fails."""
            raise RuntimeError("tool broke")

        tools = ToolSet([good_tool, bad_tool])
        engine = _make_engine(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[
                        ToolCallData(id="c1", name="good_tool", arguments={"x": "1"}),
                        ToolCallData(id="c2", name="bad_tool", arguments={"x": "2"}),
                    ],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                _text_response("Handled errors"),
            ],
            tools=tools,
            parallel_tool_execution=True,
        )

        result = await engine.run("run both")
        assert result.output == "Handled errors"
        # bad_tool error captured in memory
        messages = engine.memory.get_messages()
        tool_msgs = [m for m in messages if m.role == "tool"]
        error_msg = [m for m in tool_msgs if "Error" in m.content]
        assert len(error_msg) == 1
        assert "tool broke" in error_msg[0].content


# =========================================================================
# TestEngineSequentialWarden
# =========================================================================


class TestEngineSequentialWarden:
    """Warden review path in _execute_tool_sequential."""

    @pytest.mark.asyncio
    async def test_warden_auto_approved_executes_tool(self):
        """Warden auto-approval (reversible + auto_approve_reversible) executes inline."""
        tools = _reversible_warden_tools()
        handler = MockInterruptHandler()
        warden = Warden(handler=handler, auto_approve_reversible=True)
        engine = _make_engine(
            responses=[
                _tool_call_response("safe_action", {"target": "server-1"}),
                _text_response("Action completed"),
            ],
            tools=tools,
            warden=warden,
        )

        result = await engine.run("Do the safe thing")

        assert result.output == "Action completed"
        # Handler was NOT notified (auto-approved)
        assert len(handler.received) == 0
        # Tool was executed — check memory for tool result
        messages = engine.memory.get_messages()
        tool_msgs = [m for m in messages if m.role == "tool"]
        assert any("Executed safely on server-1" in m.content for m in tool_msgs)

    @pytest.mark.asyncio
    async def test_warden_not_auto_approved_checkpoints_and_raises(self):
        """Non-auto-approved warden tool → notify, checkpoint, raise."""
        tools = _warden_tools()
        handler = MockInterruptHandler()
        warden = Warden(handler=handler, auto_approve_reversible=True)
        store = MemoryCheckpointStore()
        engine = _make_engine(
            responses=[
                _tool_call_response("dangerous_action", {"target": "server-1"}),
            ],
            tools=tools,
            warden=warden,
            checkpoint_store=store,
        )

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await engine.run("Do the dangerous thing")

        # Handler was notified
        assert len(handler.received) == 1
        assert handler.received[0].tool_name == "dangerous_action"
        assert "warden" in handler.received[0].context

        # Checkpoint was created
        checkpoint = await store.load(exc_info.value.checkpoint_id)
        assert checkpoint is not None
        assert checkpoint.pending_tool == "dangerous_action"


# =========================================================================
# TestEngineUnifiedInterrupt
# =========================================================================


class TestEngineUnifiedInterrupt:
    """Unified interrupt path: notify + checkpoint + raise (always)."""

    @pytest.mark.asyncio
    async def test_interrupt_with_handler_notifies_and_raises(self):
        """Handler present → notify called, checkpoint saved, error raised."""
        tools = _interrupt_tools()
        handler = MockInterruptHandler()
        store = MemoryCheckpointStore()
        engine = _make_engine(
            responses=[
                _tool_call_response("delete_record", {"record_id": "42"}),
            ],
            tools=tools,
            interrupt_handler=handler,
            checkpoint_store=store,
        )

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await engine.run("Delete record 42")

        # Handler was notified
        assert len(handler.received) == 1
        assert handler.received[0].tool_name == "delete_record"
        assert handler.received[0].tool_args == {"record_id": "42"}

        # Checkpoint was created
        checkpoint = await store.load(exc_info.value.checkpoint_id)
        assert checkpoint is not None
        assert checkpoint.pending_tool == "delete_record"
        assert checkpoint.status == "pending"

    @pytest.mark.asyncio
    async def test_interrupt_without_handler_checkpoints_and_raises(self):
        """No handler → checkpoint created, error raised (no notify)."""
        tools = _interrupt_tools()
        store = MemoryCheckpointStore()
        engine = _make_engine(
            responses=[
                _tool_call_response("delete_record", {"record_id": "42"}),
            ],
            tools=tools,
            interrupt_handler=None,
            checkpoint_store=store,
        )

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await engine.run("Delete record 42")

        # Checkpoint was created
        checkpoint_id = exc_info.value.checkpoint_id
        checkpoint = await store.load(checkpoint_id)
        assert checkpoint is not None
        assert checkpoint.pending_tool == "delete_record"
        assert checkpoint.pending_args == {"record_id": "42"}
        assert checkpoint.status == "pending"

    @pytest.mark.asyncio
    async def test_notify_called_with_correct_interrupt_fields(self):
        """Interrupt object passed to notify() has correct fields."""
        tools = _interrupt_tools()
        handler = MockInterruptHandler()
        store = MemoryCheckpointStore()
        engine = _make_engine(
            responses=[
                _tool_call_response("delete_record", {"record_id": "99"}),
            ],
            tools=tools,
            interrupt_handler=handler,
            checkpoint_store=store,
            name="my-agent",
        )

        with pytest.raises(ExecutionInterruptedError):
            await engine.run("Delete 99")

        assert len(handler.received) == 1
        interrupt = handler.received[0]
        assert interrupt.tool_name == "delete_record"
        assert interrupt.tool_args == {"record_id": "99"}
        assert interrupt.name == "my-agent"
        assert interrupt.prompt == "Approve this deletion?"


# =========================================================================
# TestEngineCreateCheckpoint
# =========================================================================


class TestEngineCreateCheckpoint:
    """Checkpoint creation via _create_checkpoint."""

    @pytest.mark.asyncio
    async def test_checkpoint_saved_with_correct_state(self):
        """Checkpoint captures pending tool, args, and messages."""
        tools = _interrupt_tools()
        store = MemoryCheckpointStore()
        engine = _make_engine(
            responses=[
                _tool_call_response("delete_record", {"record_id": "7"}, call_id="tc-7"),
            ],
            tools=tools,
            interrupt_handler=None,
            checkpoint_store=store,
            name="agent-x",
        )

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await engine.run("Delete record 7")

        checkpoint = await store.load(exc_info.value.checkpoint_id)
        assert checkpoint.name == "agent-x"
        assert checkpoint.pending_tool == "delete_record"
        assert checkpoint.pending_args == {"record_id": "7"}
        assert checkpoint.pending_tool_call_id == "tc-7"
        assert checkpoint.prompt == "Approve this deletion?"
        # Messages should include the user input
        assert any(m.role == "user" for m in checkpoint.messages)
