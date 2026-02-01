"""Tests for shared RunContext across orchestration patterns."""

import pytest
from conftest import MockProvider

from tantra import Agent, RunContext, ToolSet, tool
from tantra.context import MemoryContextStore
from tantra.exceptions import ContextMergeConflictError
from tantra.orchestration import Graph, Parallel, Pipeline, Router, Swarm
from tantra.types import ProviderResponse, ToolCallData

# =============================================================================
# Helper: create agents with context-aware tools
# =============================================================================


def _make_writer_tool(key: str, value: str):
    """Create a tool that writes a key/value to RunContext."""

    @tool
    def writer(context: RunContext) -> str:
        f"""Write {key}={value} to context."""
        context.set(key, value)
        return f"wrote {key}"

    writer.name = f"write_{key}"
    return writer


def _make_reader_tool(key: str):
    """Create a tool that reads a key from RunContext."""

    @tool
    def reader(context: RunContext) -> str:
        f"""Read {key} from context."""
        val = context.get(key, "MISSING")
        context.set(f"read_{key}", val)
        return f"{key}={val}"

    reader.name = f"read_{key}"
    return reader


def _tool_call_response(tool_name: str, args: dict | None = None):
    """Create a ProviderResponse with a single tool call."""
    return ProviderResponse(
        content=None,
        tool_calls=[ToolCallData(id="c1", name=tool_name, arguments=args or {})],
        prompt_tokens=10,
        completion_tokens=5,
    )


def _text_response(text: str = "Done"):
    """Create a simple text ProviderResponse."""
    return ProviderResponse(content=text, tool_calls=None, prompt_tokens=10, completion_tokens=5)


# =============================================================================
# Pipeline
# =============================================================================


class TestPipelineContext:
    @pytest.mark.asyncio
    async def test_shared_context_across_agents(self):
        """Agent A writes to context, Agent B reads it."""
        writer = _make_writer_tool("data", "from_agent_a")
        reader = _make_reader_tool("data")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_data"), _text_response("A done")]),
            tools=ToolSet([writer]),
        )
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("read_data"), _text_response("B done")]),
            tools=ToolSet([reader]),
        )

        pipeline = Pipeline([("a", agent_a), ("b", agent_b)])
        ctx = RunContext()
        result = await pipeline.run("Go", shared_context=ctx)

        assert result.context is ctx
        assert ctx.get("data") == "from_agent_a"
        assert ctx.get("read_data") == "from_agent_a"

    @pytest.mark.asyncio
    async def test_no_shared_context_isolates_agents(self):
        """Without shared_context, agents have separate contexts."""
        writer = _make_writer_tool("data", "from_agent_a")
        reader = _make_reader_tool("data")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_data"), _text_response("A done")]),
            tools=ToolSet([writer]),
        )
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("read_data"), _text_response("B done")]),
            tools=ToolSet([reader]),
        )

        pipeline = Pipeline([("a", agent_a), ("b", agent_b)])
        result = await pipeline.run("Go")

        # No shared context — result.context is None
        assert result.context is None

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Context persists across pipeline runs via session_id."""
        writer = _make_writer_tool("counter", "1")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_counter"), _text_response("Done")]),
            tools=ToolSet([writer]),
        )

        store = MemoryContextStore()
        pipeline = Pipeline([("a", agent_a)], context_store=store)

        # Run 1: writes counter=1
        result1 = await pipeline.run("Go", session_id="sess_1")
        assert result1.context.get("counter") == "1"

        # Run 2: loads from session, context should have counter from run 1
        reader = _make_reader_tool("counter")
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("read_counter"), _text_response("Done")]),
            tools=ToolSet([reader]),
        )
        pipeline2 = Pipeline([("b", agent_b)], context_store=store)
        result2 = await pipeline2.run("Go", session_id="sess_1")
        assert result2.context.get("read_counter") == "1"


# =============================================================================
# Router
# =============================================================================


class TestRouterContext:
    @pytest.mark.asyncio
    async def test_selected_agent_receives_context(self):
        """The routed-to agent receives shared context."""
        writer = _make_writer_tool("routed", "yes")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_routed"), _text_response("A done")]),
            tools=ToolSet([writer]),
        )
        agent_b = Agent(MockProvider(responses=["B done"]))

        router = Router(
            agents={"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a",
        )
        ctx = RunContext()
        result = await router.run("Go", shared_context=ctx)

        assert result.context is ctx
        assert ctx.get("routed") == "yes"

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Context persists across router runs."""
        writer = _make_writer_tool("key", "val")
        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_key"), _text_response("Done")]),
            tools=ToolSet([writer]),
        )

        store = MemoryContextStore()
        router = Router(agents={"a": agent_a}, route_fn=lambda x: "a", context_store=store)

        await router.run("Go", session_id="r_sess")

        reader = _make_reader_tool("key")
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("read_key"), _text_response("Done")]),
            tools=ToolSet([reader]),
        )
        router2 = Router(agents={"b": agent_b}, route_fn=lambda x: "b", context_store=store)
        result2 = await router2.run("Go", session_id="r_sess")
        assert result2.context.get("read_key") == "val"


# =============================================================================
# Parallel
# =============================================================================


class TestParallelContext:
    @pytest.mark.asyncio
    async def test_explicit_shared_context(self):
        """All parallel agents write to distinct keys in shared context."""
        writer_a = _make_writer_tool("from_a", "hello")
        writer_b = _make_writer_tool("from_b", "world")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_from_a"), _text_response("A")]),
            tools=ToolSet([writer_a]),
        )
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("write_from_b"), _text_response("B")]),
            tools=ToolSet([writer_b]),
        )

        parallel = Parallel([("a", agent_a), ("b", agent_b)])
        ctx = RunContext()
        result = await parallel.run("Go", shared_context=ctx)

        assert result.context is ctx
        assert ctx.get("from_a") == "hello"
        assert ctx.get("from_b") == "world"

    @pytest.mark.asyncio
    async def test_no_shared_context_isolates(self):
        """Without shared_context, parallel agents are isolated."""
        parallel = Parallel(
            [
                ("a", Agent(MockProvider(responses=["A"]))),
                ("b", Agent(MockProvider(responses=["B"]))),
            ]
        )
        result = await parallel.run("Go")
        assert result.context is None

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Context persists across parallel runs."""
        writer = _make_writer_tool("pkey", "pval")
        agent = Agent(
            MockProvider(responses=[_tool_call_response("write_pkey"), _text_response("Done")]),
            tools=ToolSet([writer]),
        )

        store = MemoryContextStore()
        p1 = Parallel([("a", agent)], context_store=store)
        await p1.run("Go", session_id="p_sess")

        reader = _make_reader_tool("pkey")
        agent2 = Agent(
            MockProvider(responses=[_tool_call_response("read_pkey"), _text_response("Done")]),
            tools=ToolSet([reader]),
        )
        p2 = Parallel([("b", agent2)], context_store=store)
        result2 = await p2.run("Go", session_id="p_sess")
        assert result2.context.get("read_pkey") == "pval"


class TestParallelCopyPerAgent:
    """Tests for copy-per-agent merge-back behavior in Parallel."""

    @pytest.mark.asyncio
    async def test_agents_get_isolated_copies(self):
        """Each parallel agent writes to its own copy, not the shared reference."""
        # Both agents write to the SAME key with the SAME value — no conflict
        writer_a = _make_writer_tool("shared_key", "same_value")
        writer_b = _make_writer_tool("shared_key", "same_value")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_shared_key"), _text_response("A")]),
            tools=ToolSet([writer_a]),
        )
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("write_shared_key"), _text_response("B")]),
            tools=ToolSet([writer_b]),
        )

        parallel = Parallel([("a", agent_a), ("b", agent_b)])
        ctx = RunContext()
        await parallel.run("Go", shared_context=ctx)

        # Same value written by both — no conflict, merge succeeds
        assert ctx.get("shared_key") == "same_value"

    @pytest.mark.asyncio
    async def test_conflict_raises(self):
        """Two agents writing different values to the same key raises ContextMergeConflictError."""
        writer_a = _make_writer_tool("conflict_key", "value_a")
        writer_b = _make_writer_tool("conflict_key", "value_b")

        agent_a = Agent(
            MockProvider(
                responses=[_tool_call_response("write_conflict_key"), _text_response("A")]
            ),
            tools=ToolSet([writer_a]),
        )
        agent_b = Agent(
            MockProvider(
                responses=[_tool_call_response("write_conflict_key"), _text_response("B")]
            ),
            tools=ToolSet([writer_b]),
        )

        parallel = Parallel([("a", agent_a), ("b", agent_b)])
        ctx = RunContext()

        with pytest.raises(ContextMergeConflictError) as exc_info:
            await parallel.run("Go", shared_context=ctx)

        assert exc_info.value.key == "conflict_key"
        assert "a" in exc_info.value.agents
        assert "b" in exc_info.value.agents

    @pytest.mark.asyncio
    async def test_pre_existing_keys_preserved(self):
        """Pre-existing context data is available to agents and preserved after merge."""
        reader = _make_reader_tool("existing")
        agent = Agent(
            MockProvider(responses=[_tool_call_response("read_existing"), _text_response("Done")]),
            tools=ToolSet([reader]),
        )

        parallel = Parallel([("a", agent)])
        ctx = RunContext({"existing": "pre_set"})
        await parallel.run("Go", shared_context=ctx)

        # Agent read the pre-existing key
        assert ctx.get("read_existing") == "pre_set"
        # Original key still present
        assert ctx.get("existing") == "pre_set"

    @pytest.mark.asyncio
    async def test_distinct_keys_merge_cleanly(self):
        """Each agent writing to distinct keys merges without conflict."""
        writer_a = _make_writer_tool("key_a", "val_a")
        writer_b = _make_writer_tool("key_b", "val_b")
        writer_c = _make_writer_tool("key_c", "val_c")

        agent_a = Agent(
            MockProvider(responses=[_tool_call_response("write_key_a"), _text_response("A")]),
            tools=ToolSet([writer_a]),
        )
        agent_b = Agent(
            MockProvider(responses=[_tool_call_response("write_key_b"), _text_response("B")]),
            tools=ToolSet([writer_b]),
        )
        agent_c = Agent(
            MockProvider(responses=[_tool_call_response("write_key_c"), _text_response("C")]),
            tools=ToolSet([writer_c]),
        )

        parallel = Parallel([("a", agent_a), ("b", agent_b), ("c", agent_c)])
        ctx = RunContext()
        await parallel.run("Go", shared_context=ctx)

        assert ctx.get("key_a") == "val_a"
        assert ctx.get("key_b") == "val_b"
        assert ctx.get("key_c") == "val_c"


# =============================================================================
# Swarm
# =============================================================================


class TestSwarmContext:
    @pytest.mark.asyncio
    async def test_context_across_handoffs(self):
        """Context persists across agent handoffs in a swarm."""
        writer = _make_writer_tool("triage_data", "issue_123")

        # Triage agent: calls write tool, then hands off to billing via tool call
        triage_provider = MockProvider(
            responses=[
                _tool_call_response("write_triage_data"),
                _tool_call_response(
                    "transfer_to_billing",
                    {"reason": "billing issue", "summary": "customer question"},
                ),
                _text_response("Transferring to billing"),
            ]
        )

        reader = _make_reader_tool("triage_data")
        billing_provider = MockProvider(
            responses=[_tool_call_response("read_triage_data"), _text_response("Billing done")],
        )

        triage = Agent(triage_provider, tools=ToolSet([writer]))
        billing = Agent(billing_provider, tools=ToolSet([reader]))

        s = Swarm(
            agents={"triage": triage, "billing": billing},
            handoffs={"triage": ["billing"], "billing": ["triage"]},
            entry_point="triage",
        )
        ctx = RunContext()
        result = await s.run("Help", shared_context=ctx)

        assert result.context is ctx
        assert ctx.get("triage_data") == "issue_123"
        # Billing agent read triage's data
        assert ctx.get("read_triage_data") == "issue_123"

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Context persists across swarm runs via session_id."""
        writer = _make_writer_tool("swarm_key", "swarm_val")

        triage = Agent(
            MockProvider(
                responses=[_tool_call_response("write_swarm_key"), _text_response("Done")]
            ),
            tools=ToolSet([writer]),
        )

        store = MemoryContextStore()
        s = Swarm(
            agents={"triage": triage},
            entry_point="triage",
            context_store=store,
        )
        await s.run("Go", session_id="sw_sess")

        # Second run loads from session
        reader = _make_reader_tool("swarm_key")
        triage2 = Agent(
            MockProvider(responses=[_tool_call_response("read_swarm_key"), _text_response("Done")]),
            tools=ToolSet([reader]),
        )
        s2 = Swarm(
            agents={"triage": triage2},
            entry_point="triage",
            context_store=store,
        )
        result2 = await s2.run("Go", session_id="sw_sess")
        assert result2.context.get("read_swarm_key") == "swarm_val"


# =============================================================================
# Graph
# =============================================================================


class TestGraphContext:
    @pytest.mark.asyncio
    async def test_agent_nodes_share_context(self):
        """AgentNodes share RunContext across graph execution."""
        writer = _make_writer_tool("graph_data", "node1_output")
        reader = _make_reader_tool("graph_data")

        agent1 = Agent(
            MockProvider(
                responses=[_tool_call_response("write_graph_data"), _text_response("Node1 done")]
            ),
            tools=ToolSet([writer]),
        )
        agent2 = Agent(
            MockProvider(
                responses=[_tool_call_response("read_graph_data"), _text_response("Node2 done")]
            ),
            tools=ToolSet([reader]),
        )

        graph = Graph()
        graph.add_agent("node1", agent1)
        graph.add_agent("node2", agent2)
        graph.add_edge("START", "node1")
        graph.add_edge("node1", "node2")
        graph.add_edge("node2", "END")

        ctx = RunContext()
        result = await graph.run("Go", shared_context=ctx)

        assert result.context is ctx
        assert ctx.get("graph_data") == "node1_output"
        assert ctx.get("read_graph_data") == "node1_output"

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Context persists across graph runs via session_id."""
        writer = _make_writer_tool("gkey", "gval")
        agent = Agent(
            MockProvider(responses=[_tool_call_response("write_gkey"), _text_response("Done")]),
            tools=ToolSet([writer]),
        )

        store = MemoryContextStore()
        graph = Graph(context_store=store)
        graph.add_agent("n1", agent)
        graph.add_edge("START", "n1")
        graph.add_edge("n1", "END")
        await graph.run("Go", session_id="g_sess")

        reader = _make_reader_tool("gkey")
        agent2 = Agent(
            MockProvider(responses=[_tool_call_response("read_gkey"), _text_response("Done")]),
            tools=ToolSet([reader]),
        )
        graph2 = Graph(context_store=store)
        graph2.add_agent("n1", agent2)
        graph2.add_edge("START", "n1")
        graph2.add_edge("n1", "END")
        result2 = await graph2.run("Go", session_id="g_sess")
        assert result2.context.get("read_gkey") == "gval"

    @pytest.mark.asyncio
    async def test_no_shared_context(self):
        """Without shared_context, graph result context is None."""
        agent = Agent(MockProvider(responses=["Done"]))

        graph = Graph()
        graph.add_agent("n1", agent)
        graph.add_edge("START", "n1")
        graph.add_edge("n1", "END")

        result = await graph.run("Go")
        assert result.context is None


# =============================================================================
# Agent.run() context param
# =============================================================================


class TestAgentContextParam:
    @pytest.mark.asyncio
    async def test_explicit_context_used(self):
        """Agent.run(context=...) uses the provided context."""
        captured = {}

        @tool
        def check(context: RunContext) -> str:
            """Check context."""
            captured["val"] = context.get("pre_set")
            return "ok"

        tools = ToolSet([check])
        agent = Agent(
            MockProvider(responses=[_tool_call_response("check"), _text_response("Done")]),
            tools=tools,
        )

        ctx = RunContext({"pre_set": "external"})
        result = await agent.run("Go", context=ctx)

        assert result.context is ctx
        assert captured["val"] == "external"

    @pytest.mark.asyncio
    async def test_explicit_context_priority_over_session(self):
        """Explicit context takes priority over session_id loading."""
        store = MemoryContextStore()
        await store.save("sess_x", {"from_store": True})

        agent = Agent(
            MockProvider(responses=["Done"]),
            context_store=store,
        )

        ctx = RunContext({"from_explicit": True})
        result = await agent.run("Go", session_id="sess_x", context=ctx)

        assert result.context is ctx
        assert ctx.get("from_explicit") is True
        # session data was NOT loaded into this context
        assert ctx.get("from_store") is None

        # But session_id still saves
        saved = await store.load("sess_x")
        assert saved.get("from_explicit") is True
