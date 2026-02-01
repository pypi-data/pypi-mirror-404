"""Tests for Swarm orchestration pattern."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from conftest import MemoryCheckpointStore, MockProvider

from tantra import Agent, ToolSet, tool
from tantra.checkpoints import Checkpoint
from tantra.engine import ExecutionInterruptedError
from tantra.exceptions import ConfigurationError
from tantra.intheloop import InterruptResponse
from tantra.orchestration.swarm import (
    Handoff,
    Swarm,
    SwarmDetail,
    SwarmStep,
    _deserialize_step,
    _serialize_step,
    swarm,
)
from tantra.types import LogEntry, LogType, ProviderResponse, RunMetadata, ToolCallData

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent(responses=None, system_prompt="", tools=None):
    """Create an Agent backed by MockProvider."""
    return Agent(
        provider=MockProvider(responses=responses or ["Hello!"]),
        system_prompt=system_prompt,
        tools=tools,
    )


def _make_run_result(output="ok", trace=None):
    """Build a minimal RunResult-like object for _detect_handoff."""
    return SimpleNamespace(
        output=output,
        trace=trace or [],
        metadata=RunMetadata(
            run_id=uuid4(),
            total_tokens=10,
            prompt_tokens=5,
            completion_tokens=5,
            estimated_cost=0.0,
            duration_ms=1.0,
            tool_calls_count=0,
        ),
    )


def _make_trace_entry(entry_type, data):
    """Create a LogEntry for trace testing."""
    return LogEntry(
        run_id=uuid4(),
        type=entry_type,
        data=data,
    )


# =========================================================================
# TestSwarmInit
# =========================================================================


class TestSwarmInit:
    """Constructor validation."""

    def test_valid_init(self):
        a = _make_agent()
        b = _make_agent()
        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
        )
        assert s.entry_point == "a"
        assert set(s.agents.keys()) == {"a", "b"}

    def test_default_entry_point(self):
        a = _make_agent()
        b = _make_agent()
        s = Swarm(agents={"first": a, "second": b})
        assert s.entry_point == "first"

    def test_default_handoffs_all_to_all(self):
        a, b, c = _make_agent(), _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b, "c": c})
        h = s.handoffs
        assert set(h["a"]) == {"b", "c"}
        assert set(h["b"]) == {"a", "c"}
        assert set(h["c"]) == {"a", "b"}

    def test_invalid_entry_point(self):
        a = _make_agent()
        with pytest.raises(ValueError, match="Entry point"):
            Swarm(agents={"a": a}, entry_point="missing")

    def test_invalid_handoff_source(self):
        a = _make_agent()
        with pytest.raises(ValueError, match="Handoff source"):
            Swarm(agents={"a": a}, handoffs={"missing": ["a"]})

    def test_invalid_handoff_target(self):
        a = _make_agent()
        b = _make_agent()
        with pytest.raises(ValueError, match="Handoff target"):
            Swarm(agents={"a": a, "b": b}, handoffs={"a": ["missing"]})


# =========================================================================
# TestSwarmProperties
# =========================================================================


class TestSwarmProperties:
    """Read-only property accessors."""

    def test_orchestration_type(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        assert s.orchestration_type == "swarm"

    def test_agents_returns_copy(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        agents = s.agents
        agents["c"] = _make_agent()
        assert "c" not in s.agents

    def test_entry_point(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"x": a, "y": b}, entry_point="y")
        assert s.entry_point == "y"

    def test_handoffs_returns_copy(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        h = s.handoffs
        h["a"].append("c")
        assert "c" not in s.handoffs["a"]


# =========================================================================
# TestSwarmWrapAgent
# =========================================================================


class TestSwarmWrapAgent:
    """Agent wrapping with handoff tools."""

    def test_wrapped_agent_has_handoff_tools(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        wrapped = s._wrapped_agents["a"]
        tool_names = {t.name for t in wrapped.tools}
        assert "transfer_to_b" in tool_names
        assert "consult_b" in tool_names
        assert "list_available_agents" in tool_names

    def test_no_targets_returns_original(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": []})
        # b has no targets, should be the original agent
        assert s._wrapped_agents["b"] is b

    def test_preserves_provider_and_system_prompt(self):
        provider = MockProvider()
        a = Agent(provider=provider, system_prompt="I am A")
        b = _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        wrapped = s._wrapped_agents["a"]
        assert wrapped.provider is provider
        assert "I am A" in wrapped.system_prompt

    def test_enhanced_system_prompt_mentions_targets(self):
        a = Agent(provider=MockProvider(), system_prompt="Base prompt")
        b = _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        wrapped = s._wrapped_agents["a"]
        assert "transfer_to_" in wrapped.system_prompt
        assert "consult_" in wrapped.system_prompt
        assert "b" in wrapped.system_prompt

    def test_existing_tools_merged(self):
        @tool
        def my_tool(x: str) -> str:
            """A custom tool."""
            return x

        a = Agent(provider=MockProvider(), tools=ToolSet([my_tool]))
        b = _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        wrapped = s._wrapped_agents["a"]
        tool_names = {t.name for t in wrapped.tools}
        assert "my_tool" in tool_names
        assert "transfer_to_b" in tool_names


# =========================================================================
# TestSwarmHandoffTools
# =========================================================================


class TestSwarmHandoffTools:
    """Handoff, consult, and list tool creation and execution."""

    @pytest.mark.asyncio
    async def test_transfer_returns_handoff_dict(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        handoff_fn = s._create_handoff_function("b")
        result = await handoff_fn("billing issue", "user asked about invoice")
        assert isinstance(result, dict)
        assert result["__handoff__"] is True
        assert result["target"] == "b"
        assert result["reason"] == "billing issue"
        assert result["summary"] == "user asked about invoice"

    @pytest.mark.asyncio
    async def test_consult_calls_agent_and_returns_response(self):
        target_agent = _make_agent(responses=["The answer is 42"])
        a = _make_agent()
        s = Swarm(
            agents={"a": a, "target": target_agent},
            handoffs={"a": ["target"], "target": ["a"]},
        )
        consult_fn = s._create_consult_function("target")
        result = await consult_fn("What is the answer?")
        assert "[Response from target]" in result
        assert "The answer is 42" in result

    @pytest.mark.asyncio
    async def test_consult_handles_error(self):
        """Consult returns error message if agent.run() fails."""
        a = _make_agent()
        # Create agent that will fail
        failing_agent = _make_agent()
        s = Swarm(
            agents={"a": a, "fail": failing_agent},
            handoffs={"a": ["fail"], "fail": ["a"]},
        )
        consult_fn = s._create_consult_function("fail")
        # Patch the original (not wrapped) agent to raise
        with patch.object(s._agents["fail"], "run", side_effect=RuntimeError("boom")):
            result = await consult_fn("question")
        assert "[Error consulting fail]" in result
        assert "boom" in result

    @pytest.mark.asyncio
    async def test_list_agents_shows_all_with_you_marker(self):
        a = Agent(provider=MockProvider(), system_prompt="Handle billing questions")
        b = Agent(provider=MockProvider(), system_prompt="Handle tech support")
        s = Swarm(
            agents={"billing": a, "support": b},
            handoffs={"billing": ["support"], "support": ["billing"]},
        )
        list_fn = s._create_list_agents_function("billing")
        result = await list_fn()
        assert "Available agents:" in result
        assert "billing (you)" in result
        assert "support" in result
        assert "Handle billing" in result


# =========================================================================
# TestSwarmDetectHandoff
# =========================================================================


class TestSwarmDetectHandoff:
    """Handoff detection from structured trace entries."""

    def test_detect_from_trace_entry(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        handoff_data = json.dumps(
            {
                "__handoff__": True,
                "target": "b",
                "reason": "needs billing",
                "summary": "invoice question",
            }
        )
        entry = _make_trace_entry(LogType.TOOL_RESULT, {"result": handoff_data})
        result = _make_run_result(output="some output", trace=[entry])
        handoff = s._detect_handoff(result)
        assert handoff is not None
        assert handoff.target == "b"
        assert handoff.reason == "needs billing"
        assert handoff.context["summary"] == "invoice question"

    def test_no_handoff_returns_none(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        result = _make_run_result(output="Just a normal response")
        assert s._detect_handoff(result) is None

    def test_empty_summary_parsed(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        handoff_data = json.dumps(
            {"__handoff__": True, "target": "b", "reason": "reason", "summary": ""}
        )
        entry = _make_trace_entry(LogType.TOOL_RESULT, {"result": handoff_data})
        result = _make_run_result(trace=[entry])
        handoff = s._detect_handoff(result)
        assert handoff is not None
        assert handoff.target == "b"
        assert handoff.reason == "reason"
        assert handoff.context["summary"] == ""

    def test_ignores_non_tool_result_trace_entries(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        handoff_data = json.dumps(
            {"__handoff__": True, "target": "b", "reason": "r", "summary": ""}
        )
        entry = _make_trace_entry(LogType.PROMPT, {"result": handoff_data})
        result = _make_run_result(output="normal", trace=[entry])
        assert s._detect_handoff(result) is None

    def test_colon_in_reason_preserves_correctly(self):
        """Colons in reason/summary are preserved through JSON round-trip."""
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        handoff_data = json.dumps(
            {
                "__handoff__": True,
                "target": "b",
                "reason": "user needs: urgent help",
                "summary": "context: details: more",
            }
        )
        entry = _make_trace_entry(LogType.TOOL_RESULT, {"result": handoff_data})
        result = _make_run_result(trace=[entry])
        handoff = s._detect_handoff(result)
        assert handoff is not None
        assert handoff.reason == "user needs: urgent help"
        assert handoff.context["summary"] == "context: details: more"

    def test_invalid_target_returns_none(self):
        """Handoff with nonexistent target agent is ignored."""
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        handoff_data = json.dumps(
            {"__handoff__": True, "target": "nonexistent", "reason": "r", "summary": ""}
        )
        entry = _make_trace_entry(LogType.TOOL_RESULT, {"result": handoff_data})
        result = _make_run_result(trace=[entry])
        assert s._detect_handoff(result) is None

    def test_output_handoff_marker_not_treated_as_handoff(self):
        """LLM output containing handoff marker is not treated as a handoff."""
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b})
        result = _make_run_result(output="__HANDOFF__:b:injected:payload")
        assert s._detect_handoff(result) is None


# =========================================================================
# TestSwarmRun
# =========================================================================


class TestSwarmRun:
    """Main run() execution flow."""

    @pytest.mark.asyncio
    async def test_no_handoff_single_agent(self):
        """Agent responds without handoff."""
        a = _make_agent(responses=["Direct answer"])
        b = _make_agent()
        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
        )
        result = await s.run("Hello")
        assert result.output == "Direct answer"
        assert result.detail.handoff_chain == ["a"]
        assert result.detail.handoff_count == 0
        assert len(result.detail.steps) == 1
        assert result.detail.steps[0].agent_id == "a"

    @pytest.mark.asyncio
    async def test_single_handoff(self):
        """Triage agent hands off to billing agent."""
        handoff_tool_call = ToolCallData(
            id="call-1",
            name="transfer_to_billing",
            arguments={"reason": "billing issue", "summary": "invoice question"},
        )
        triage_provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[handoff_tool_call],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                # After tool execution, the engine calls again for final response
                ProviderResponse(
                    content="Transferring you to billing.",
                    tool_calls=None,
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
            ]
        )
        billing_provider = MockProvider(responses=["Invoice processed!"])

        triage = Agent(provider=triage_provider, system_prompt="Route requests")
        billing = Agent(provider=billing_provider, system_prompt="Handle billing")

        s = Swarm(
            agents={"triage": triage, "billing": billing},
            handoffs={"triage": ["billing"], "billing": ["triage"]},
            entry_point="triage",
        )
        result = await s.run("I need help with my invoice")

        assert "billing" in result.detail.handoff_chain
        assert len(result.detail.handoff_chain) >= 2
        assert result.detail.handoff_count >= 1

    @pytest.mark.asyncio
    async def test_max_handoffs_prevents_infinite_loop(self):
        """Max handoffs limit prevents infinite agent ping-pong."""
        handoff_to_b = ToolCallData(
            id="call-1",
            name="transfer_to_b",
            arguments={"reason": "go to b", "summary": ""},
        )
        handoff_to_a = ToolCallData(
            id="call-2",
            name="transfer_to_a",
            arguments={"reason": "go to a", "summary": ""},
        )
        # Each agent run consumes 2 provider calls: tool_call + text.
        # Provide enough pairs so every run produces a handoff.
        tool_call_b = ProviderResponse(
            content=None, tool_calls=[handoff_to_b], prompt_tokens=5, completion_tokens=5
        )
        tool_call_a = ProviderResponse(
            content=None, tool_calls=[handoff_to_a], prompt_tokens=5, completion_tokens=5
        )
        text_resp = ProviderResponse(
            content="done", tool_calls=None, prompt_tokens=5, completion_tokens=5
        )
        a_provider = MockProvider(
            responses=[tool_call_b, text_resp, tool_call_b, text_resp, tool_call_b, text_resp]
        )
        b_provider = MockProvider(
            responses=[tool_call_a, text_resp, tool_call_a, text_resp, tool_call_a, text_resp]
        )

        a = Agent(provider=a_provider, system_prompt="Agent A")
        b = Agent(provider=b_provider, system_prompt="Agent B")

        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
            max_handoffs=3,
        )
        result = await s.run("ping pong")

        # Exactly 3 handoffs: a→b, b→a, a→b, then b runs and is stopped
        assert result.detail.handoff_count == 3
        assert result.detail.handoff_chain == ["a", "b", "a", "b"]

    @pytest.mark.asyncio
    async def test_error_during_agent_run(self):
        """Error in agent run is captured in step."""
        a = _make_agent()
        b = _make_agent()
        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
        )
        # Patch the provider (shared across clones) to raise
        with patch.object(
            s._wrapped_agents["a"].provider, "complete", side_effect=RuntimeError("agent failed")
        ):
            result = await s.run("trigger error")

        assert len(result.detail.steps) == 1
        assert result.detail.steps[0].error is not None
        assert "agent failed" in str(result.detail.steps[0].error)

    @pytest.mark.asyncio
    async def test_result_fields_populated(self):
        """RunResult with SwarmDetail has all expected fields."""
        a = _make_agent(responses=["Done"])
        s = Swarm(agents={"a": a}, handoffs={"a": []})
        result = await s.run("Hello")

        assert isinstance(result.detail, SwarmDetail)
        assert result.output == "Done"
        assert result.detail.orchestration_type == "swarm"
        assert result.metadata.total_tokens >= 0
        assert result.metadata.estimated_cost >= 0
        assert result.metadata.duration_ms >= 0
        assert len(result.trace) > 0
        assert result.detail.handoff_chain == ["a"]

    @pytest.mark.asyncio
    async def test_swarm_convenience_function(self):
        """swarm() factory creates working Swarm."""
        a = _make_agent(responses=["A says hi"])
        b = _make_agent()
        s = swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
        )
        assert isinstance(s, Swarm)
        result = await s.run("hi")
        assert result.output == "A says hi"

    def test_swarm_factory_forwards_all_parameters(self):
        """swarm() factory passes through all configuration."""
        a = _make_agent()
        b = _make_agent()
        s = swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="b",
            max_handoffs=5,
            preserve_memory=False,
            name="test-swarm",
        )
        assert s.entry_point == "b"
        assert s._max_handoffs == 5
        assert s._preserve_memory is False
        assert s._name == "test-swarm"

    @pytest.mark.asyncio
    async def test_concurrent_runs_are_independent(self):
        """Two concurrent runs on the same Swarm don't corrupt each other."""
        a = _make_agent(responses=["Response A"])
        b = _make_agent(responses=["Response B"])
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})

        result1, result2 = await asyncio.gather(
            s.run("first request"),
            s.run("second request"),
        )

        # Both runs complete without error
        assert result1.detail.success
        assert result2.detail.success
        assert result1.output == "Response A"
        assert result2.output == "Response A"
        # Each has its own independent step history
        assert len(result1.detail.steps) == 1
        assert len(result2.detail.steps) == 1


# =========================================================================
# TestSwarmDataclasses
# =========================================================================


class TestSwarmDataclasses:
    """Handoff, SwarmStep, SwarmDetail dataclasses."""

    def test_handoff_creation(self):
        h = Handoff(target="billing", reason="billing issue", context={"key": "val"})
        assert h.target == "billing"
        assert h.reason == "billing issue"

    def test_swarm_step_with_handoff(self):
        step = SwarmStep(
            agent_id="triage",
            input="help",
            output="transferring",
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5,
                estimated_cost=0.0,
                duration_ms=1.0,
                tool_calls_count=0,
            ),
            duration_ms=100,
            handoff_to="billing",
            handoff_reason="billing question",
        )
        assert step.handoff_to == "billing"

    def test_swarm_detail_handoff_count(self):
        d = SwarmDetail(
            steps=[],
            orchestration_type="swarm",
            handoff_chain=["triage", "billing", "support"],
        )
        assert d.handoff_count == 2

    def test_swarm_detail_no_handoffs(self):
        d = SwarmDetail(
            steps=[],
            orchestration_type="swarm",
            handoff_chain=["triage"],
        )
        assert d.handoff_count == 0

    def test_swarm_detail_empty_chain(self):
        d = SwarmDetail(
            steps=[],
            orchestration_type="swarm",
            handoff_chain=[],
        )
        assert d.handoff_count == 0


# =========================================================================
# TestSwarmClone
# =========================================================================


class TestSwarmClone:
    """Swarm clone() for session isolation."""

    def test_clone_returns_new_instance(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
            max_handoffs=5,
            name="test-swarm",
        )
        cloned = s.clone()
        assert isinstance(cloned, Swarm)
        assert cloned is not s
        assert cloned._name == "test-swarm"
        assert cloned._entry_point == "a"
        assert cloned._max_handoffs == 5

    def test_clone_shares_agents(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        cloned = s.clone()
        assert cloned._agents["a"] is a
        assert cloned._agents["b"] is b

    def test_clone_rebuilds_wrapped_agents(self):
        a, b = _make_agent(), _make_agent()
        s = Swarm(agents={"a": a, "b": b}, handoffs={"a": ["b"], "b": ["a"]})
        cloned = s.clone()
        # Wrapped agents are rebuilt, not shared
        assert cloned._wrapped_agents is not s._wrapped_agents

    def test_clone_passes_checkpoint_store(self):
        a = _make_agent()
        store = MemoryCheckpointStore()
        s = Swarm(agents={"a": a}, handoffs={"a": []}, checkpoint_store=store)
        cloned = s.clone()
        assert cloned._checkpoint_store is store

    def test_clone_overrides_checkpoint_store(self):
        a = _make_agent()
        store1 = MemoryCheckpointStore()
        store2 = MemoryCheckpointStore()
        s = Swarm(agents={"a": a}, handoffs={"a": []}, checkpoint_store=store1)
        cloned = s.clone(checkpoint_store=store2)
        assert cloned._checkpoint_store is store2

    @pytest.mark.asyncio
    async def test_clone_is_functional(self):
        a = _make_agent(responses=["Cloned response"])
        s = Swarm(agents={"a": a}, handoffs={"a": []})
        cloned = s.clone()
        result = await cloned.run("Hello")
        assert result.output == "Cloned response"
        assert result.detail.handoff_chain == ["a"]


# =========================================================================
# TestSwarmSerialization
# =========================================================================


class TestSwarmSerialization:
    """Step serialization/deserialization for checkpoints."""

    def test_serialize_roundtrip(self):
        step = SwarmStep(
            agent_id="a",
            input="hello",
            output="world",
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5,
                estimated_cost=0.01,
                duration_ms=100.0,
                tool_calls_count=1,
            ),
            duration_ms=100.0,
            handoff_to="b",
            handoff_reason="needs billing",
        )
        data = _serialize_step(step)
        restored = _deserialize_step(data)
        assert restored.agent_id == "a"
        assert restored.input == "hello"
        assert restored.output == "world"
        assert restored.handoff_to == "b"
        assert restored.handoff_reason == "needs billing"
        assert restored.metadata.total_tokens == 10
        assert restored.duration_ms == 100.0
        assert restored.error is None

    def test_serialize_with_error(self):
        step = SwarmStep(
            agent_id="a",
            input="hi",
            output="",
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                estimated_cost=0,
                duration_ms=0,
                tool_calls_count=0,
            ),
            duration_ms=0,
            error=RuntimeError("boom"),
        )
        data = _serialize_step(step)
        assert data["error"] == "boom"
        restored = _deserialize_step(data)
        assert restored.error is not None
        assert "boom" in str(restored.error)

    def test_serialize_no_handoff(self):
        step = SwarmStep(
            agent_id="a",
            input="hi",
            output="bye",
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=5,
                prompt_tokens=2,
                completion_tokens=3,
                estimated_cost=0,
                duration_ms=50.0,
                tool_calls_count=0,
            ),
            duration_ms=50.0,
        )
        data = _serialize_step(step)
        assert data["handoff_to"] is None
        assert data["handoff_reason"] is None
        restored = _deserialize_step(data)
        assert restored.handoff_to is None


# =========================================================================
# TestSwarmCheckpoints
# =========================================================================


class TestSwarmCheckpoints:
    """Checkpoint save/resume for swarm orchestration."""

    @pytest.mark.asyncio
    async def test_no_checkpoint_store_no_checkpoints(self):
        """Swarm works without checkpoint store (existing behavior)."""
        a = _make_agent(responses=["Done"])
        s = Swarm(agents={"a": a}, handoffs={"a": []})
        assert s._checkpoint_store is None
        result = await s.run("Hello")
        assert result.output == "Done"

    @pytest.mark.asyncio
    async def test_progress_checkpoint_saved_after_handoff(self):
        """Checkpoint store saves swarm_progress after a handoff."""
        handoff_tool_call = ToolCallData(
            id="call-1",
            name="transfer_to_billing",
            arguments={"reason": "billing issue", "summary": "invoice question"},
        )
        triage_provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[handoff_tool_call],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content="Transferring you.",
                    tool_calls=None,
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
            ]
        )
        billing_provider = MockProvider(responses=["Invoice processed!"])

        triage = Agent(provider=triage_provider, system_prompt="Route requests")
        billing = Agent(provider=billing_provider, system_prompt="Handle billing")

        store = MemoryCheckpointStore()
        s = Swarm(
            agents={"triage": triage, "billing": billing},
            handoffs={"triage": ["billing"], "billing": ["triage"]},
            entry_point="triage",
            checkpoint_store=store,
        )
        await s.run("I need help with my invoice")

        # Verify checkpoint was saved
        pending = await store.list_pending()
        # After successful run, checkpoints remain pending (they're progress markers)
        assert len(pending) >= 1
        cp = pending[0]
        assert cp.checkpoint_type == "swarm_progress"
        assert cp.context["current_agent"] == "billing"
        assert "triage" in cp.context["handoff_chain"]
        assert "billing" in cp.context["handoff_chain"]

    @pytest.mark.asyncio
    async def test_interrupt_checkpoint_wraps_agent_checkpoint(self):
        """Interrupt in agent creates swarm_interrupt with agent_checkpoint_id."""
        store = MemoryCheckpointStore()
        a = _make_agent(responses=["Hello"])
        b = _make_agent()

        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
            checkpoint_store=store,
        )

        # The run loop calls clone() on wrapped_agents, then .run() on the clone.
        # Patch clone() to return a mock whose run() raises.
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(
            side_effect=ExecutionInterruptedError("agent-cp-123", "Approve delete?")
        )
        with patch.object(s._wrapped_agents["a"], "clone", return_value=mock_agent):
            with pytest.raises(ExecutionInterruptedError) as exc_info:
                await s.run("trigger interrupt")

        # The swarm should have re-raised with its own checkpoint ID
        swarm_cp_id = exc_info.value.checkpoint_id
        assert swarm_cp_id != "agent-cp-123"  # wrapped in swarm checkpoint
        assert exc_info.value.prompt == "Approve delete?"

        # Verify checkpoint was saved
        cp = await store.load(swarm_cp_id)
        assert cp is not None
        assert cp.checkpoint_type == "swarm_interrupt"
        assert cp.context["agent_checkpoint_id"] == "agent-cp-123"
        assert cp.context["interrupted_agent"] == "a"

    @pytest.mark.asyncio
    async def test_interrupt_without_store_propagates_raw_error(self):
        """Without checkpoint store, ExecutionInterruptedError passes through."""
        a = _make_agent()
        s = Swarm(agents={"a": a}, handoffs={"a": []}, entry_point="a")

        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(
            side_effect=ExecutionInterruptedError("raw-cp-id", "Approve?")
        )
        with patch.object(s._wrapped_agents["a"], "clone", return_value=mock_agent):
            with pytest.raises(ExecutionInterruptedError) as exc_info:
                await s.run("trigger")

        # The original checkpoint ID passes through
        assert exc_info.value.checkpoint_id == "raw-cp-id"

    @pytest.mark.asyncio
    async def test_resume_from_progress(self):
        """Resume from swarm_progress continues from the correct agent."""
        store = MemoryCheckpointStore()

        # Set up agents
        billing_provider = MockProvider(responses=["Invoice resolved!"])
        billing = Agent(provider=billing_provider, system_prompt="Handle billing")
        triage = _make_agent(responses=["routing"])

        s = Swarm(
            agents={"triage": triage, "billing": billing},
            handoffs={"triage": ["billing"], "billing": ["triage"]},
            entry_point="triage",
            checkpoint_store=store,
        )

        # Create a progress checkpoint as if triage had just handed off to billing
        run_id = uuid4()
        triage_step = SwarmStep(
            agent_id="triage",
            input="help with invoice",
            output="Transferring to billing",
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=15,
                prompt_tokens=10,
                completion_tokens=5,
                estimated_cost=0.01,
                duration_ms=100.0,
                tool_calls_count=1,
            ),
            duration_ms=100.0,
            handoff_to="billing",
            handoff_reason="billing issue",
        )

        checkpoint = Checkpoint(
            name="swarm",
            run_id=run_id,
            checkpoint_type="swarm_progress",
            messages=[],
            context={
                "current_agent": "billing",
                "current_input": "[Handoff from previous agent]\nReason: billing issue\n",
                "handoff_chain": ["triage", "billing"],
                "handoff_count": 1,
                "steps": [_serialize_step(triage_step)],
                "total_tokens": 15,
                "total_cost": 0.01,
                "context_data": None,
                "swarm_name": None,
            },
            status="pending",
        )
        cp_id = await store.save(checkpoint)

        # Resume
        result = await s.resume(cp_id)

        assert result.output == "Invoice resolved!"
        assert result.detail.handoff_chain == ["triage", "billing"]
        # Should have the original step plus the resumed billing step
        assert len(result.detail.steps) == 2
        assert result.detail.steps[0].agent_id == "triage"
        assert result.detail.steps[1].agent_id == "billing"

        # Checkpoint should be marked completed
        updated = await store.load(cp_id)
        assert updated.status == "completed"

    @pytest.mark.asyncio
    async def test_resume_from_interrupt(self):
        """Resume from swarm_interrupt resumes the agent and continues."""
        store = MemoryCheckpointStore()

        a = _make_agent(responses=["Done after approval"])
        b = _make_agent()
        s = Swarm(
            agents={"a": a, "b": b},
            handoffs={"a": ["b"], "b": ["a"]},
            entry_point="a",
            checkpoint_store=store,
        )

        run_id = uuid4()
        checkpoint = Checkpoint(
            name="swarm",
            run_id=run_id,
            checkpoint_type="swarm_interrupt",
            messages=[],
            context={
                "current_agent": "a",
                "current_input": "delete user 123",
                "handoff_chain": ["a"],
                "handoff_count": 0,
                "steps": [],
                "total_tokens": 0,
                "total_cost": 0.0,
                "context_data": None,
                "swarm_name": None,
                "agent_checkpoint_id": "agent-cp-456",
                "interrupted_agent": "a",
            },
            status="pending",
        )
        cp_id = await store.save(checkpoint)

        # Mock agent.resume to return a normal result
        mock_result = _make_run_result(output="User deleted", trace=[])
        with patch.object(s._wrapped_agents["a"], "clone") as mock_clone:
            mock_agent = AsyncMock()
            mock_agent.resume = AsyncMock(return_value=mock_result)
            mock_clone.return_value = mock_agent

            response = InterruptResponse(value=True, proceed=True)
            result = await s.resume(cp_id, response=response)

        assert result.output == "User deleted"
        mock_agent.resume.assert_awaited_once_with("agent-cp-456", response)

        # Checkpoint should be marked completed
        updated = await store.load(cp_id)
        assert updated.status == "completed"

    @pytest.mark.asyncio
    async def test_resume_no_store_raises(self):
        """resume() without checkpoint store raises ConfigurationError."""
        a = _make_agent()
        s = Swarm(agents={"a": a}, handoffs={"a": []})
        with pytest.raises(ConfigurationError, match="No checkpoint store"):
            await s.resume("some-id")

    @pytest.mark.asyncio
    async def test_resume_checkpoint_not_found(self):
        """resume() with missing checkpoint raises ValueError."""
        store = MemoryCheckpointStore()
        a = _make_agent()
        s = Swarm(agents={"a": a}, handoffs={"a": []}, checkpoint_store=store)
        with pytest.raises(ValueError, match="not found"):
            await s.resume("nonexistent-id")

    @pytest.mark.asyncio
    async def test_resume_unknown_type_raises(self):
        """resume() with unknown checkpoint type raises ValueError."""
        store = MemoryCheckpointStore()
        a = _make_agent()
        s = Swarm(agents={"a": a}, handoffs={"a": []}, checkpoint_store=store)
        checkpoint = Checkpoint(
            name="swarm",
            run_id=uuid4(),
            checkpoint_type="unknown_type",
            messages=[],
            context={},
            status="pending",
        )
        cp_id = await store.save(checkpoint)
        with pytest.raises(ValueError, match="Expected checkpoint_type"):
            await s.resume(cp_id)

    @pytest.mark.asyncio
    async def test_resume_interrupt_without_response_raises(self):
        """resume() for interrupt without response raises ValueError."""
        store = MemoryCheckpointStore()
        a = _make_agent()
        s = Swarm(agents={"a": a}, handoffs={"a": []}, checkpoint_store=store)
        checkpoint = Checkpoint(
            name="swarm",
            run_id=uuid4(),
            checkpoint_type="swarm_interrupt",
            messages=[],
            context={
                "current_agent": "a",
                "current_input": "hi",
                "handoff_chain": ["a"],
                "handoff_count": 0,
                "steps": [],
                "total_tokens": 0,
                "total_cost": 0.0,
                "context_data": None,
                "agent_checkpoint_id": "cp-1",
                "interrupted_agent": "a",
            },
            status="pending",
        )
        cp_id = await store.save(checkpoint)
        with pytest.raises(ValueError, match="InterruptResponse required"):
            await s.resume(cp_id)

    def test_factory_accepts_checkpoint_store(self):
        """swarm() factory passes checkpoint_store through."""
        a = _make_agent()
        store = MemoryCheckpointStore()
        s = swarm(
            agents={"a": a},
            handoffs={"a": []},
            checkpoint_store=store,
        )
        assert s._checkpoint_store is store
