"""Tests for Graph-based Workflow Engine."""

from uuid import uuid4

import pytest
from conftest import MemoryCheckpointStore, MockProvider

from tantra import (
    AbortedError,
    Agent,
    AgentNode,
    ConfigurationError,
    Edge,
    EdgeCondition,
    ExecutionInterruptedError,
    FunctionNode,
    Graph,
    GraphBuilder,
    GraphState,
    InterruptResponse,
    RouterNode,
    ToolSet,
    create_graph,
    tool,
)
from tantra.checkpoints import Checkpoint
from tantra.context import RunContext
from tantra.types import ProviderResponse, ToolCallData

# =============================================================================
# GraphState Tests
# =============================================================================


class TestGraphState:
    """Tests for GraphState."""

    def test_create_state(self):
        """Create initial state."""
        state = GraphState(input="Hello")
        assert state.input == "Hello"
        assert state.current_output == ""
        assert state.iteration == 0

    def test_add_result(self):
        """Add node result to state."""
        state = GraphState(input="Hello")
        state.add_result("node1", "Output 1")

        assert state.current_output == "Output 1"
        assert state.node_outputs["node1"] == "Output 1"
        assert len(state.history) == 1

    def test_get_output(self):
        """Get specific node output."""
        state = GraphState(input="Hello")
        state.add_result("node1", "Output 1")
        state.add_result("node2", "Output 2")

        assert state.get_output("node1") == "Output 1"
        assert state.get_output("node2") == "Output 2"
        assert state.get_output("node3") is None

    def test_to_dict(self):
        """Convert state to dictionary."""
        state = GraphState(input="Hello", metadata={"key": "value"})
        state.add_result("node1", "Output")

        data = state.to_dict()
        assert data["input"] == "Hello"
        assert data["metadata"]["key"] == "value"
        assert len(data["history"]) == 1


# =============================================================================
# Edge Tests
# =============================================================================


class TestEdge:
    """Tests for Edge."""

    def test_always_condition(self):
        """Edge with ALWAYS condition."""
        edge = Edge(source="a", target="b", condition=EdgeCondition.ALWAYS)
        state = GraphState(input="test")

        assert edge.should_traverse(state, success=True, tool_called=False)
        assert edge.should_traverse(state, success=False, tool_called=False)

    def test_on_success_condition(self):
        """Edge with ON_SUCCESS condition."""
        edge = Edge(source="a", target="b", condition=EdgeCondition.ON_SUCCESS)
        state = GraphState(input="test")

        assert edge.should_traverse(state, success=True, tool_called=False)
        assert not edge.should_traverse(state, success=False, tool_called=False)

    def test_on_failure_condition(self):
        """Edge with ON_FAILURE condition."""
        edge = Edge(source="a", target="b", condition=EdgeCondition.ON_FAILURE)
        state = GraphState(input="test")

        assert not edge.should_traverse(state, success=True, tool_called=False)
        assert edge.should_traverse(state, success=False, tool_called=False)

    def test_on_tool_call_condition(self):
        """Edge with ON_TOOL_CALL condition."""
        edge = Edge(source="a", target="b", condition=EdgeCondition.ON_TOOL_CALL)
        state = GraphState(input="test")

        assert edge.should_traverse(state, success=True, tool_called=True)
        assert not edge.should_traverse(state, success=True, tool_called=False)

    def test_custom_condition(self):
        """Edge with custom condition function."""

        def check_keyword(state: GraphState) -> bool:
            return "important" in state.current_output.lower()

        edge = Edge(
            source="a",
            target="b",
            condition=EdgeCondition.CUSTOM,
            condition_fn=check_keyword,
        )

        state = GraphState(input="test")
        state.current_output = "This is important"
        assert edge.should_traverse(state, success=True, tool_called=False)

        state.current_output = "This is not"
        assert not edge.should_traverse(state, success=True, tool_called=False)


# =============================================================================
# Node Tests
# =============================================================================


class TestAgentNode:
    """Tests for AgentNode."""

    @pytest.mark.asyncio
    async def test_execute_agent(self):
        """Execute agent node."""
        agent = Agent(MockProvider(responses=["Agent output"]))
        node = AgentNode(id="test", agent=agent)

        state = GraphState(input="Hello")
        output, success, tool_called = await node.execute(state)

        assert output == "Agent output"
        assert success is True

    @pytest.mark.asyncio
    async def test_execute_with_input_transform(self):
        """Execute with custom input transform."""
        agent = Agent(MockProvider(responses=["Transformed output"]))
        node = AgentNode(
            id="test",
            agent=agent,
            input_transform=lambda s: f"Transform: {s.input}",
        )

        state = GraphState(input="Original")
        output, success, _ = await node.execute(state)

        assert success is True


class TestRouterNode:
    """Tests for RouterNode."""

    @pytest.mark.asyncio
    async def test_route_to_target(self):
        """Router selects correct target."""
        node = RouterNode(
            id="router",
            routes={
                "path_a": lambda s: "a" in s.current_output,
                "path_b": lambda s: "b" in s.current_output,
            },
            default_route="default",
        )

        state = GraphState(input="test")
        state.current_output = "contains a"
        target, success, _ = await node.execute(state)

        assert target == "path_a"
        assert success is True

    @pytest.mark.asyncio
    async def test_route_default(self):
        """Router uses default when no match."""
        node = RouterNode(
            id="router",
            routes={"path_a": lambda s: False},
            default_route="default",
        )

        state = GraphState(input="test")
        target, success, _ = await node.execute(state)

        assert target == "default"


class TestFunctionNode:
    """Tests for FunctionNode."""

    @pytest.mark.asyncio
    async def test_sync_function(self):
        """Execute sync function."""

        def transform(state: GraphState) -> str:
            return state.input.upper()

        node = FunctionNode(id="func", func=transform)
        state = GraphState(input="hello")
        output, success, _ = await node.execute(state)

        assert output == "HELLO"
        assert success is True

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Execute async function."""

        async def async_transform(state: GraphState) -> str:
            return f"Async: {state.input}"

        node = FunctionNode(id="func", func=async_transform)
        state = GraphState(input="test")
        output, success, _ = await node.execute(state)

        assert output == "Async: test"
        assert success is True


# =============================================================================
# Graph Tests
# =============================================================================


class TestGraph:
    """Tests for Graph."""

    @pytest.mark.asyncio
    async def test_simple_linear_graph(self):
        """Simple linear graph execution."""
        agent1 = Agent(MockProvider(responses=["Output 1"]))
        agent2 = Agent(MockProvider(responses=["Output 2"]))

        graph = Graph()
        graph.add_agent("node1", agent1)
        graph.add_agent("node2", agent2)
        graph.add_edge("START", "node1")
        graph.add_edge("node1", "node2")
        graph.add_edge("node2", "END")

        result = await graph.run("Input")

        assert result.detail.success
        assert result.output == "Output 2"
        assert result.detail.nodes_executed == ["node1", "node2"]

    @pytest.mark.asyncio
    async def test_graph_with_router(self):
        """Graph with routing logic."""
        agent_a = Agent(MockProvider(responses=["Path A output"]))
        agent_b = Agent(MockProvider(responses=["Path B output"]))

        graph = Graph()
        graph.add_agent("agent_a", agent_a)
        graph.add_agent("agent_b", agent_b)
        graph.add_router(
            "router",
            routes={
                "agent_a": lambda s: "a" in s.input.lower(),
                "agent_b": lambda s: "b" in s.input.lower(),
            },
            default="agent_a",
        )

        graph.add_edge("START", "router")
        graph.add_edge("agent_a", "END")
        graph.add_edge("agent_b", "END")

        # Test routing to A
        result = await graph.run("Go to A please")
        assert "Path A" in result.output

    @pytest.mark.asyncio
    async def test_graph_conditional_edges(self):
        """Graph with conditional edges."""
        agent1 = Agent(MockProvider(responses=["Success output"]))
        agent2 = Agent(MockProvider(responses=["Fallback output"]))

        graph = Graph()
        graph.add_agent("main", agent1)
        graph.add_agent("fallback", agent2)

        graph.add_edge("START", "main")
        graph.add_edge("main", "END", condition=EdgeCondition.ON_SUCCESS)
        graph.add_edge("main", "fallback", condition=EdgeCondition.ON_FAILURE)
        graph.add_edge("fallback", "END")

        result = await graph.run("Input")
        assert result.output == "Success output"

    @pytest.mark.asyncio
    async def test_graph_function_node(self):
        """Graph with function node."""

        def preprocess(state: GraphState) -> str:
            return f"Preprocessed: {state.input}"

        agent = Agent(MockProvider(responses=["Final output"]))

        graph = Graph()
        graph.add_function("preprocess", preprocess)
        graph.add_agent("agent", agent)

        graph.add_edge("START", "preprocess")
        graph.add_edge("preprocess", "agent")
        graph.add_edge("agent", "END")

        result = await graph.run("Raw input")
        assert "preprocess" in result.detail.nodes_executed

    @pytest.mark.asyncio
    async def test_graph_max_iterations(self):
        """Graph respects max iterations."""
        # Create a cyclic graph that would loop forever
        agent = Agent(MockProvider(responses=["Loop"] * 100))

        graph = Graph(max_iterations=5)
        graph.add_agent("loop", agent)
        graph.add_edge("START", "loop")
        graph.add_edge("loop", "loop")  # Self-loop

        result = await graph.run("Input")
        assert result.detail.total_iterations <= 5

    @pytest.mark.asyncio
    async def test_graph_no_start_node_error(self):
        """Error when no start node defined."""
        graph = Graph()
        graph.add_agent("node", Agent(MockProvider()))

        with pytest.raises(ValueError, match="No start node"):
            await graph.run("Input")

    def test_graph_builder(self):
        """Build graph with fluent API."""
        agent = Agent(MockProvider())

        graph = (
            GraphBuilder("test")
            .add_agent("a", agent)
            .add_agent("b", agent)
            .edge("START", "a")
            .edge("a", "b")
            .edge("b", "END")
            .build()
        )

        assert "a" in graph._nodes
        assert "b" in graph._nodes
        assert len(graph._edges) == 3


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_graph(self):
        """create_graph returns builder."""
        builder = create_graph("test_graph")
        assert isinstance(builder, GraphBuilder)


# =============================================================================
# Integration Tests
# =============================================================================


class TestGraphIntegration:
    """Integration tests for graph orchestration."""

    @pytest.mark.asyncio
    async def test_content_pipeline(self):
        """Multi-stage content pipeline."""
        researcher = Agent(MockProvider(responses=["Research findings: AI is growing"]))
        writer = Agent(MockProvider(responses=["Article: AI Growth Story"]))
        editor = Agent(MockProvider(responses=["Final: Polished AI Article"]))

        graph = (
            create_graph("content_pipeline")
            .add_agent("research", researcher)
            .add_agent("write", writer)
            .add_agent("edit", editor)
            .edge("START", "research")
            .edge("research", "write")
            .edge("write", "edit")
            .edge("edit", "END")
            .build()
        )

        result = await graph.run("Write about AI")

        assert result.detail.success
        assert "Polished" in result.output
        assert result.detail.nodes_executed == ["research", "write", "edit"]

    @pytest.mark.asyncio
    async def test_conditional_workflow(self):
        """Workflow with conditional branching."""
        classifier = Agent(MockProvider(responses=["Category: Technical"]))
        tech_handler = Agent(MockProvider(responses=["Technical response"]))
        general_handler = Agent(MockProvider(responses=["General response"]))

        graph = Graph()
        graph.add_agent("classify", classifier)
        graph.add_agent("tech", tech_handler)
        graph.add_agent("general", general_handler)

        graph.add_router(
            "route",
            routes={
                "tech": lambda s: "technical" in s.current_output.lower(),
                "general": lambda s: True,
            },
        )

        graph.add_edge("START", "classify")
        graph.add_edge("classify", "route")
        graph.add_edge("tech", "END")
        graph.add_edge("general", "END")

        result = await graph.run("How do I fix this bug?")
        assert "Technical" in result.detail.state.node_outputs.get("classify", "")

    @pytest.mark.asyncio
    async def test_graph_state_persists(self):
        """State persists through graph execution."""

        def add_metadata(state: GraphState) -> str:
            state.metadata["processed"] = True
            return state.input

        agent = Agent(MockProvider(responses=["Done"]))

        graph = Graph()
        graph.add_function("meta", add_metadata)
        graph.add_agent("process", agent)

        graph.add_edge("START", "meta")
        graph.add_edge("meta", "process")
        graph.add_edge("process", "END")

        result = await graph.run("Input")
        assert result.detail.state.metadata.get("processed") is True


# =============================================================================
# Graph Checkpointing Tests
# =============================================================================


class TestGraphCheckpointing:
    """Tests for graph-level checkpointing and crash recovery."""

    def test_from_dict_roundtrip(self):
        """to_dict() -> from_dict() preserves all fields; trace is empty."""
        run_id = uuid4()
        state = GraphState(
            input="Hello",
            current_output="World",
            metadata={"key": "value"},
            iteration=3,
            node_outputs={"node1": "out1"},
            errors=["err1"],
            run_id=run_id,
        )
        state.add_result("node2", "out2")

        data = state.to_dict()
        restored = GraphState.from_dict(data)

        assert restored.input == "Hello"
        assert restored.current_output == "out2"
        assert restored.metadata == {"key": "value"}
        assert restored.iteration == 3
        assert restored.node_outputs["node1"] == "out1"
        assert restored.node_outputs["node2"] == "out2"
        assert restored.errors == ["err1"]
        assert restored.run_id == run_id
        assert restored.trace == []
        assert len(restored.history) == 1

    def test_from_dict_minimal(self):
        """Only input + run_id required for from_dict."""
        rid = uuid4()
        data = {"input": "test", "run_id": str(rid)}
        restored = GraphState.from_dict(data)

        assert restored.input == "test"
        assert restored.current_output == ""
        assert restored.history == []
        assert restored.metadata == {}
        assert restored.iteration == 0
        assert restored.node_outputs == {}
        assert restored.errors == []
        assert restored.run_id == rid
        assert restored.trace == []

    @pytest.mark.asyncio
    async def test_checkpoints_saved_per_node(self):
        """Checkpoints are created after each node; last one is 'completed'."""
        store = MemoryCheckpointStore()
        agent1 = Agent(MockProvider(responses=["Output 1"]))
        agent2 = Agent(MockProvider(responses=["Output 2"]))

        graph = Graph(checkpoint_store=store)
        graph.add_agent("step1", agent1)
        graph.add_agent("step2", agent2)
        graph.add_edge("START", "step1")
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", "END")

        result = await graph.run("Input")

        assert result.detail.success
        assert result.output == "Output 2"

        all_checkpoints = list(store._checkpoints.values())
        assert len(all_checkpoints) >= 2

        for cp in all_checkpoints:
            assert cp.checkpoint_type == "graph_progress"

        # Last checkpoint should be completed
        completed = [c for c in all_checkpoints if c.status == "completed"]
        assert len(completed) >= 1

        # Intermediate checkpoints should be pending
        pending = [c for c in all_checkpoints if c.status == "pending"]
        assert len(pending) >= 1

    @pytest.mark.asyncio
    async def test_no_checkpoints_without_store(self):
        """Graph without checkpoint store runs normally with no checkpoints."""
        agent1 = Agent(MockProvider(responses=["Output 1"]))
        agent2 = Agent(MockProvider(responses=["Output 2"]))

        graph = Graph()
        graph.add_agent("step1", agent1)
        graph.add_agent("step2", agent2)
        graph.add_edge("START", "step1")
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", "END")

        result = await graph.run("Input")

        assert result.detail.success
        assert result.output == "Output 2"
        assert result.detail.nodes_executed == ["step1", "step2"]

    @pytest.mark.asyncio
    async def test_resume_from_mid_graph(self):
        """Resume from a mid-graph checkpoint skips already-executed nodes."""
        store = MemoryCheckpointStore()

        agent1 = Agent(MockProvider(responses=["Out1"]))
        agent2 = Agent(MockProvider(responses=["Out2"]))
        agent3 = Agent(MockProvider(responses=["Out3"]))

        # Run the full graph first to populate checkpoints
        graph = Graph(name="pipeline", checkpoint_store=store)
        graph.add_agent("step1", agent1)
        graph.add_agent("step2", agent2)
        graph.add_agent("step3", agent3)
        graph.add_edge("START", "step1")
        graph.add_edge("step1", "step2")
        graph.add_edge("step2", "step3")
        graph.add_edge("step3", "END")

        await graph.run("Input")

        # Find the checkpoint recorded after step1 (next_node=step2)
        all_cps = list(store._checkpoints.values())
        step1_cp = None
        for cp in all_cps:
            if cp.context.get("next_node") == "step2":
                step1_cp = cp
                break

        assert step1_cp is not None

        # Reset it to pending so resume can use it
        await store.update(step1_cp.id, status="pending")

        # Create a fresh graph with same topology but fresh agents
        fresh_agent2 = Agent(MockProvider(responses=["Fresh2"]))
        fresh_agent3 = Agent(MockProvider(responses=["Fresh3"]))

        graph2 = Graph(name="pipeline", checkpoint_store=store)
        graph2.add_agent("step1", Agent(MockProvider(responses=["Unused"])))
        graph2.add_agent("step2", fresh_agent2)
        graph2.add_agent("step3", fresh_agent3)
        graph2.add_edge("START", "step1")
        graph2.add_edge("step1", "step2")
        graph2.add_edge("step2", "step3")
        graph2.add_edge("step3", "END")

        result = await graph2.resume(step1_cp.id)

        assert result.detail.success
        assert result.output == "Fresh3"
        # step2 and step3 should have been executed
        assert "step2" in result.detail.nodes_executed
        assert "step3" in result.detail.nodes_executed
        # step1 was already done before the checkpoint
        assert result.detail.nodes_executed.count("step1") <= 1

    @pytest.mark.asyncio
    async def test_resume_restores_context(self):
        """Resume restores the RunContext from the checkpoint."""
        store = MemoryCheckpointStore()

        agent1 = Agent(MockProvider(responses=["Done1"]))
        agent2 = Agent(MockProvider(responses=["Done2"]))

        graph = Graph(name="ctx_graph", checkpoint_store=store)
        graph.add_agent("a", agent1)
        graph.add_agent("b", agent2)
        graph.add_edge("START", "a")
        graph.add_edge("a", "b")
        graph.add_edge("b", "END")

        ctx = RunContext({"key": "value"})
        await graph.run("Input", shared_context=ctx)

        # Find a checkpoint that has context_data
        all_cps = list(store._checkpoints.values())
        cp_with_ctx = None
        for cp in all_cps:
            if cp.context.get("context_data") is not None:
                cp_with_ctx = cp
                break

        assert cp_with_ctx is not None
        assert cp_with_ctx.context["context_data"]["key"] == "value"

        # Reset and resume
        await store.update(cp_with_ctx.id, status="pending")

        graph2 = Graph(name="ctx_graph", checkpoint_store=store)
        graph2.add_agent("a", Agent(MockProvider(responses=["X"])))
        graph2.add_agent("b", Agent(MockProvider(responses=["Y"])))
        graph2.add_edge("START", "a")
        graph2.add_edge("a", "b")
        graph2.add_edge("b", "END")

        result = await graph2.resume(cp_with_ctx.id)
        assert result.context is not None
        assert result.context.get("key") == "value"

    @pytest.mark.asyncio
    async def test_resume_nonexistent_raises(self):
        """ValueError for missing checkpoint."""
        store = MemoryCheckpointStore()
        graph = Graph(checkpoint_store=store)
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        with pytest.raises(ValueError, match="Checkpoint not found"):
            await graph.resume("nonexistent-id")

    @pytest.mark.asyncio
    async def test_resume_without_store_raises(self):
        """ConfigurationError when no store is available."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        with pytest.raises(ConfigurationError, match="No checkpoint store"):
            await graph.resume("some-id")

    @pytest.mark.asyncio
    async def test_resume_wrong_type_raises(self):
        """ValueError for checkpoint with wrong type."""
        store = MemoryCheckpointStore()
        graph = Graph(checkpoint_store=store)
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        # Manually save a checkpoint with wrong type
        wrong_cp = Checkpoint(
            name="test",
            run_id=uuid4(),
            checkpoint_type="interrupt",
            messages=[],
            context={},
        )
        cp_id = await store.save(wrong_cp)

        with pytest.raises(ValueError, match="graph_progress"):
            await graph.resume(cp_id)

    @pytest.mark.asyncio
    async def test_resume_cyclic_graph(self):
        """Checkpoints are saved for each iteration of a cyclic graph."""
        store = MemoryCheckpointStore()

        # Create a loop: process -> evaluate (router) -> process or done
        call_count = 0

        def process_fn(state: GraphState) -> str:
            nonlocal call_count
            call_count += 1
            state.metadata["count"] = call_count
            return f"Processed {call_count}"

        graph = Graph(name="loop", max_iterations=10, checkpoint_store=store)
        graph.add_function("process", process_fn)
        graph.add_router(
            "evaluate",
            routes={
                "process": lambda s: s.metadata.get("count", 0) < 3,
                "done": lambda s: s.metadata.get("count", 0) >= 3,
            },
        )
        graph.add_function("done", lambda s: f"Final: {s.current_output}")

        graph.add_edge("START", "process")
        graph.add_edge("process", "evaluate")
        graph.add_edge("done", "END")

        result = await graph.run("Go")

        assert result.detail.success
        assert call_count == 3

        # Should have checkpoints for each process iteration
        all_cps = list(store._checkpoints.values())
        assert len(all_cps) >= 3  # At least one per process node execution


# =============================================================================
# Graph Interrupt Tests
# =============================================================================


def _make_interrupt_tool():
    """Create a tool that requires interrupt approval."""

    @tool(interrupt="Approve this action?")
    def dangerous_action(task: str) -> str:
        """Perform a dangerous action that needs approval."""
        return f"Executed: {task}"

    return dangerous_action


def _make_interrupt_agent(store):
    """Create an agent that will trigger an interrupt on the first call,
    then return a final answer on resume."""
    interrupt_tool = _make_interrupt_tool()

    # First response: LLM asks to call the interrupt tool
    tool_call = ToolCallData(
        id="call-001",
        name="dangerous_action",
        arguments={"task": "delete records"},
    )
    provider = MockProvider(
        responses=[
            ProviderResponse(
                content=None,
                tool_calls=[tool_call],
                prompt_tokens=10,
                completion_tokens=5,
            ),
            # After resume, the tool result is added and the LLM responds
            ProviderResponse(
                content="Action completed successfully",
                tool_calls=None,
                prompt_tokens=15,
                completion_tokens=10,
            ),
        ]
    )

    return Agent(
        provider,
        tools=ToolSet([interrupt_tool]),
        checkpoint_store=store,
        name="interrupt_agent",
    )


class TestGraphInterrupt:
    """Tests for agent interrupt handling within graph nodes."""

    @pytest.mark.asyncio
    async def test_agent_interrupt_pauses_graph(self):
        """An agent interrupt pauses the entire graph and saves a graph_interrupt checkpoint."""
        store = MemoryCheckpointStore()

        pre_agent = Agent(MockProvider(responses=["Pre-processed"]))
        interrupt_agent = _make_interrupt_agent(store)
        post_agent = Agent(MockProvider(responses=["Final output"]))

        graph = Graph(name="interrupt_pipeline", checkpoint_store=store)
        graph.add_agent("pre", pre_agent)
        graph.add_agent("action", interrupt_agent)
        graph.add_agent("post", post_agent)
        graph.add_edge("START", "pre")
        graph.add_edge("pre", "action")
        graph.add_edge("action", "post")
        graph.add_edge("post", "END")

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await graph.run("Do something dangerous")

        # The error should carry a graph-level checkpoint ID
        graph_cp_id = exc_info.value.checkpoint_id
        assert exc_info.value.prompt == "Approve this action?"

        # Find the graph_interrupt checkpoint
        graph_cp = await store.load(graph_cp_id)
        assert graph_cp is not None
        assert graph_cp.checkpoint_type == "graph_interrupt"
        assert graph_cp.context["interrupted_node_id"] == "action"
        assert "agent_checkpoint_id" in graph_cp.context

        # The agent checkpoint should also exist
        agent_cp_id = graph_cp.context["agent_checkpoint_id"]
        agent_cp = await store.load(agent_cp_id)
        assert agent_cp is not None
        assert agent_cp.checkpoint_type == "interrupt"

    @pytest.mark.asyncio
    async def test_agent_interrupt_resume_continues_graph(self):
        """Full round-trip: run -> interrupt -> resume -> graph completes."""
        store = MemoryCheckpointStore()

        pre_agent = Agent(MockProvider(responses=["Pre-processed"]))
        interrupt_agent = _make_interrupt_agent(store)
        post_agent = Agent(MockProvider(responses=["Final output"]))

        graph = Graph(name="interrupt_pipeline", checkpoint_store=store)
        graph.add_agent("pre", pre_agent)
        graph.add_agent("action", interrupt_agent)
        graph.add_agent("post", post_agent)
        graph.add_edge("START", "pre")
        graph.add_edge("pre", "action")
        graph.add_edge("action", "post")
        graph.add_edge("post", "END")

        # Run until interrupt
        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await graph.run("Do something dangerous")

        graph_cp_id = exc_info.value.checkpoint_id

        # Resume with approval
        result = await graph.resume(
            graph_cp_id,
            response=InterruptResponse(proceed=True),
        )

        assert result.detail.success
        assert result.output == "Final output"
        # pre was executed before interrupt, action resumed, post executed after
        assert "pre" in result.detail.nodes_executed
        assert "action" in result.detail.nodes_executed
        assert "post" in result.detail.nodes_executed

    @pytest.mark.asyncio
    async def test_agent_interrupt_resume_abort(self):
        """Resume with proceed=False raises AbortedError."""
        store = MemoryCheckpointStore()

        interrupt_agent = _make_interrupt_agent(store)

        graph = Graph(name="abort_graph", checkpoint_store=store)
        graph.add_agent("action", interrupt_agent)
        graph.add_edge("START", "action")
        graph.add_edge("action", "END")

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await graph.run("Do something")

        graph_cp_id = exc_info.value.checkpoint_id

        with pytest.raises(AbortedError):
            await graph.resume(
                graph_cp_id,
                response=InterruptResponse(proceed=False, reason="Too risky"),
            )

    @pytest.mark.asyncio
    async def test_agent_interrupt_without_graph_store_propagates(self):
        """Without a graph checkpoint store, the agent's interrupt propagates directly."""
        agent_store = MemoryCheckpointStore()
        interrupt_agent = _make_interrupt_agent(agent_store)

        # Graph has NO checkpoint_store
        graph = Graph(name="no_store_graph")
        graph.add_agent("action", interrupt_agent)
        graph.add_edge("START", "action")
        graph.add_edge("action", "END")

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await graph.run("Do something")

        # The checkpoint_id should be the agent-level one (not a graph-level one)
        agent_cp = await agent_store.load(exc_info.value.checkpoint_id)
        assert agent_cp is not None
        assert agent_cp.checkpoint_type == "interrupt"

    @pytest.mark.asyncio
    async def test_resume_graph_interrupt_missing_response_raises(self):
        """Resuming a graph_interrupt checkpoint without response raises ValueError."""
        store = MemoryCheckpointStore()
        interrupt_agent = _make_interrupt_agent(store)

        graph = Graph(name="needs_response", checkpoint_store=store)
        graph.add_agent("action", interrupt_agent)
        graph.add_edge("START", "action")
        graph.add_edge("action", "END")

        with pytest.raises(ExecutionInterruptedError) as exc_info:
            await graph.run("Do something")

        graph_cp_id = exc_info.value.checkpoint_id

        with pytest.raises(ValueError, match="InterruptResponse required"):
            await graph.resume(graph_cp_id)


# =============================================================================
# Conditional Edge Tests
# =============================================================================


class TestConditionalEdge:
    """Tests for conditional_edge (dynamic target resolution)."""

    @pytest.mark.asyncio
    async def test_conditional_edge_routes_correctly(self):
        """conditional_edge picks the correct target based on state."""
        agent_a = Agent(MockProvider(responses=["From A"]))
        agent_b = Agent(MockProvider(responses=["From B"]))

        def pick_target(state: GraphState) -> str:
            if "route_a" in state.current_output.lower():
                return "agent_a"
            return "agent_b"

        def classify(state: GraphState) -> str:
            return "route_a"

        graph = (
            GraphBuilder("conditional_test")
            .add_function("classify", classify)
            .add_agent("agent_a", agent_a)
            .add_agent("agent_b", agent_b)
            .edge("START", "classify")
            .conditional_edge("classify", pick_target)
            .edge("agent_a", "END")
            .edge("agent_b", "END")
            .build()
        )

        result = await graph.run("test input")
        assert result.detail.success
        assert result.output == "From A"
        assert "agent_a" in result.detail.nodes_executed

    @pytest.mark.asyncio
    async def test_conditional_edge_returns_end(self):
        """conditional_edge can return 'END' to terminate the graph."""

        def always_end(state: GraphState) -> str:
            return "END"

        def step(state: GraphState) -> str:
            return "processed"

        graph = Graph()
        graph.add_function("step", step)
        graph.add_edge("START", "step")
        graph.add_conditional_edge("step", always_end)

        result = await graph.run("input")
        assert result.detail.success
        assert result.output == "processed"

    @pytest.mark.asyncio
    async def test_conditional_edge_via_graph_direct(self):
        """add_conditional_edge on Graph works directly."""
        agent_a = Agent(MockProvider(responses=["Path A"]))
        agent_b = Agent(MockProvider(responses=["Path B"]))

        graph = Graph()
        graph.add_agent("a", agent_a)
        graph.add_agent("b", agent_b)
        graph.add_edge("START", "a")
        graph.add_conditional_edge("a", lambda s: "b")
        graph.add_edge("b", "END")

        result = await graph.run("input")
        assert result.output == "Path B"


# =============================================================================
# Edge Priority Tests
# =============================================================================


class TestEdgePriority:
    """Tests for edge priority ordering."""

    @pytest.mark.asyncio
    async def test_higher_priority_edge_wins(self):
        """Higher priority edge is evaluated first."""
        agent = Agent(MockProvider(responses=["Output"]))

        graph = Graph()
        graph.add_agent("main", agent)
        graph.add_agent("fallback", Agent(MockProvider(responses=["Fallback"])))
        graph.add_agent("preferred", Agent(MockProvider(responses=["Preferred"])))

        graph.add_edge("START", "main")
        # ALWAYS edge with low priority
        graph.add_edge("main", "fallback", condition=EdgeCondition.ALWAYS, priority=0)
        # ON_SUCCESS edge with high priority
        graph.add_edge("main", "preferred", condition=EdgeCondition.ON_SUCCESS, priority=10)
        graph.add_edge("fallback", "END")
        graph.add_edge("preferred", "END")

        result = await graph.run("input")
        assert result.output == "Preferred"
        assert "preferred" in result.detail.nodes_executed

    @pytest.mark.asyncio
    async def test_equal_priority_preserves_insertion_order(self):
        """Edges with equal priority maintain insertion order."""
        agent = Agent(MockProvider(responses=["Output"]))

        graph = Graph()
        graph.add_agent("main", agent)
        graph.add_agent("first", Agent(MockProvider(responses=["First"])))
        graph.add_agent("second", Agent(MockProvider(responses=["Second"])))

        graph.add_edge("START", "main")
        graph.add_edge("main", "first", condition=EdgeCondition.ON_SUCCESS)
        graph.add_edge("main", "second", condition=EdgeCondition.ON_SUCCESS)
        graph.add_edge("first", "END")
        graph.add_edge("second", "END")

        result = await graph.run("input")
        assert result.output == "First"

    def test_priority_field_default(self):
        """Edge priority defaults to 0."""
        edge = Edge(source="a", target="b")
        assert edge.priority == 0

    def test_priority_sorting(self):
        """_get_outgoing_edges returns edges sorted by priority descending."""
        graph = Graph()
        graph.add_agent("main", Agent(MockProvider()))
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_agent("b", Agent(MockProvider()))

        graph.add_edge("main", "a", priority=1)
        graph.add_edge("main", "b", priority=10)

        edges = graph._get_outgoing_edges("main")
        assert edges[0].target == "b"
        assert edges[1].target == "a"


# =============================================================================
# Router Checkpointing Tests
# =============================================================================


class TestRouterCheckpointing:
    """Tests for router node checkpointing."""

    @pytest.mark.asyncio
    async def test_router_creates_checkpoint(self):
        """Router node execution saves a checkpoint."""
        store = MemoryCheckpointStore()

        agent_a = Agent(MockProvider(responses=["Path A result"]))

        graph = Graph(checkpoint_store=store)
        graph.add_router(
            "router",
            routes={"agent_a": lambda s: True},
            default="agent_b",
        )
        graph.add_agent("agent_a", agent_a)
        graph.add_agent("agent_b", Agent(MockProvider(responses=["Path B"])))
        graph.add_edge("START", "router")
        graph.add_edge("agent_a", "END")
        graph.add_edge("agent_b", "END")

        result = await graph.run("test")

        assert result.detail.success
        assert "router" in result.detail.nodes_executed

        all_cps = list(store._checkpoints.values())
        router_cps = [cp for cp in all_cps if cp.context.get("next_node") == "agent_a"]
        assert len(router_cps) >= 1

    @pytest.mark.asyncio
    async def test_router_recorded_in_state(self):
        """Router decision is recorded in state.node_outputs."""
        agent_a = Agent(MockProvider(responses=["Done"]))

        graph = Graph()
        graph.add_router(
            "router",
            routes={"agent_a": lambda s: True},
        )
        graph.add_agent("agent_a", agent_a)
        graph.add_edge("START", "router")
        graph.add_edge("agent_a", "END")

        result = await graph.run("test")

        assert result.detail.state.node_outputs.get("router") == "agent_a"


# =============================================================================
# Transform Application Tests
# =============================================================================


class TestTransformApplication:
    """Tests for edge transform_fn applied outside _get_next_node."""

    @pytest.mark.asyncio
    async def test_transform_applied_to_current_output(self):
        """Edge transform_fn modifies current_output when edge is traversed."""
        agent1 = Agent(MockProvider(responses=["raw output"]))
        agent2 = Agent(MockProvider(responses=["final"]))

        graph = Graph()
        graph.add_agent("step1", agent1)
        graph.add_agent("step2", agent2)
        graph.add_edge("START", "step1")
        graph.add_edge("step1", "step2", transform_fn=lambda s: s.upper())
        graph.add_edge("step2", "END")

        result = await graph.run("input")
        assert result.detail.success
        # After step1 transform, current_output becomes "RAW OUTPUT"
        # step2 runs and produces "final"
        assert result.output == "final"

    def test_get_next_node_does_not_mutate_state(self):
        """_get_next_node returns edge info without mutating state."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_agent("b", Agent(MockProvider()))
        graph.add_edge("a", "b", transform_fn=lambda s: s.upper())

        state = GraphState(input="test", current_output="hello")

        next_node, matched_edge = graph._get_next_node("a", state, success=True, tool_called=False)

        assert state.current_output == "hello"
        assert next_node == "b"
        assert matched_edge is not None
        assert matched_edge.transform_fn is not None


# =============================================================================
# Graph Validation Tests
# =============================================================================


class TestGraphValidation:
    """Tests for graph validation."""

    def test_validate_dangling_edge_source(self):
        """Validation catches edge source that is not a registered node."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph._edges.append(Edge(source="nonexistent", target="a"))
        graph.add_edge("a", "END")

        errors = graph.validate()
        assert any("nonexistent" in e for e in errors)

    def test_validate_dangling_edge_target(self):
        """Validation catches edge target that is not a registered node."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "nonexistent")

        errors = graph.validate()
        assert any("nonexistent" in e for e in errors)

    def test_validate_custom_edge_missing_condition_fn(self):
        """Validation catches CUSTOM edge without condition_fn."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_agent("b", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph._edges.append(Edge(source="a", target="b", condition=EdgeCondition.CUSTOM))
        graph.add_edge("b", "END")

        errors = graph.validate()
        assert any("CUSTOM" in e and "condition_fn" in e for e in errors)

    def test_validate_conditional_edge_missing_fn(self):
        """Validation catches CONDITIONAL edge without target_fn."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph._edges.append(Edge(source="a", target="", condition=EdgeCondition.CONDITIONAL))

        errors = graph.validate()
        assert any("CONDITIONAL" in e and "target_fn" in e for e in errors)

    def test_validate_node_no_outgoing_edges(self):
        """Validation catches non-end node with no outgoing edges."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_agent("orphan", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        errors = graph.validate()
        assert any("orphan" in e and "no outgoing" in e for e in errors)

    def test_validate_no_start_node(self):
        """Validation catches missing start node."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))

        errors = graph.validate()
        assert any("start node" in e.lower() for e in errors)

    def test_validate_start_node_not_registered(self):
        """Validation catches start node pointing to non-existent node."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.set_entry_point("nonexistent")
        graph.add_edge("a", "END")

        errors = graph.validate()
        assert any("nonexistent" in e for e in errors)

    def test_validate_good_graph(self):
        """Valid graph produces no errors."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_agent("b", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "b")
        graph.add_edge("b", "END")

        errors = graph.validate()
        assert errors == []

    def test_validate_good_graph_with_router(self):
        """Valid graph with router produces no errors."""
        graph = Graph()
        graph.add_router("router", routes={"a": lambda s: True}, default="b")
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_agent("b", Agent(MockProvider()))
        graph.add_edge("START", "router")
        graph.add_edge("a", "END")
        graph.add_edge("b", "END")

        errors = graph.validate()
        assert errors == []

    def test_validate_cyclic_graph_is_valid(self):
        """Cyclic graphs are valid (no cycle detection)."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "a")
        graph.add_edge("a", "END", condition=EdgeCondition.ON_SUCCESS)

        errors = graph.validate()
        assert errors == []

    @pytest.mark.asyncio
    async def test_run_validates_before_execution(self):
        """Graph.run() validates the graph and raises ConfigurationError."""
        graph = Graph()
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "nonexistent")

        with pytest.raises(ConfigurationError, match="validation errors"):
            await graph.run("input")

    def test_builder_build_validates(self):
        """GraphBuilder.build() validates and raises ConfigurationError."""
        builder = GraphBuilder("test")
        builder.add_agent("a", Agent(MockProvider()))
        builder.edge("START", "a")
        builder.edge("a", "nonexistent")

        with pytest.raises(ConfigurationError, match="validation errors"):
            builder.build()


# =============================================================================
# Graph Clone Tests
# =============================================================================


class TestGraphClone:
    """Graph clone() for session isolation."""

    def test_clone_returns_new_instance(self):
        graph = Graph(name="test-graph", max_iterations=10)
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        cloned = graph.clone()
        assert isinstance(cloned, Graph)
        assert cloned is not graph
        assert cloned.name == "test-graph"
        assert cloned.max_iterations == 10

    def test_clone_shares_topology(self):
        graph = Graph(name="g")
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        cloned = graph.clone()
        assert cloned._nodes is graph._nodes
        assert cloned._edges is graph._edges
        assert cloned._start_node == graph._start_node
        assert cloned._end_nodes is graph._end_nodes

    def test_clone_accepts_checkpoint_store(self):
        graph = Graph(name="g")
        graph.add_agent("a", Agent(MockProvider()))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        store = MemoryCheckpointStore()
        cloned = graph.clone(checkpoint_store=store)
        assert cloned._checkpoint_store is store
        assert cloned._checkpoint_store is not graph._checkpoint_store

    @pytest.mark.asyncio
    async def test_clone_is_functional(self):
        graph = Graph(name="g")
        graph.add_agent("a", Agent(MockProvider(responses=["Output"])))
        graph.add_edge("START", "a")
        graph.add_edge("a", "END")

        cloned = graph.clone()
        result = await cloned.run("input")
        assert result.detail.success
        assert result.output == "Output"
