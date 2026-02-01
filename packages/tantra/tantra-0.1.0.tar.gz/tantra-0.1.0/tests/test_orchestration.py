"""Tests for Multi-Agent Orchestration."""

from uuid import uuid4

import pytest
from conftest import MockProvider

from tantra import (
    Agent,
    AgentStep,
    OrchestrationDetail,
    Parallel,
    Pipeline,
    Router,
    chain,
    fan_out,
    select,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def agent_a():
    """Create mock agent A."""
    provider = MockProvider(responses=["Response from A"])
    return Agent(provider, name="agent_a")


@pytest.fixture
def agent_b():
    """Create mock agent B."""
    provider = MockProvider(responses=["Response from B"])
    return Agent(provider, name="agent_b")


@pytest.fixture
def agent_c():
    """Create mock agent C."""
    provider = MockProvider(responses=["Response from C"])
    return Agent(provider, name="agent_c")


# =============================================================================
# Pipeline Tests
# =============================================================================


class TestPipeline:
    """Tests for Pipeline orchestrator."""

    @pytest.mark.asyncio
    async def test_basic_pipeline(self, agent_a, agent_b):
        """Basic pipeline execution."""
        pipeline = Pipeline(
            [
                ("step1", agent_a),
                ("step2", agent_b),
            ]
        )

        result = await pipeline.run("Start")

        assert result.detail.success
        assert len(result.detail.steps) == 2
        assert result.detail.steps[0].agent_id == "step1"
        assert result.detail.steps[1].agent_id == "step2"
        assert result.detail.orchestration_type == "pipeline"

    @pytest.mark.asyncio
    async def test_pipeline_output_flows(self):
        """Output from one agent flows to the next."""
        agent1 = Agent(MockProvider(responses=["STEP1_OUTPUT"]))
        agent2 = Agent(MockProvider(responses=["STEP2_OUTPUT"]))

        pipeline = Pipeline([agent1, agent2])
        result = await pipeline.run("Initial input")

        # First agent gets initial input
        assert result.detail.steps[0].input == "Initial input"
        # Second agent gets first agent's output
        assert result.detail.steps[1].input == "STEP1_OUTPUT"
        # Final output is last agent's output
        assert result.output == "STEP2_OUTPUT"

    @pytest.mark.asyncio
    async def test_pipeline_with_transform(self):
        """Pipeline with custom transform function."""
        agent1 = Agent(MockProvider(responses=["output1"]))
        agent2 = Agent(MockProvider(responses=["output2"]))

        def transform(name: str, output: str) -> str:
            return f"[transformed:{name}] {output}"

        pipeline = Pipeline(
            agents=[("a", agent1), ("b", agent2)],
            transform_fn=transform,
        )

        result = await pipeline.run("start")

        assert "[transformed:a]" in result.detail.steps[1].input

    @pytest.mark.asyncio
    async def test_pipeline_stops_on_error(self):
        """Pipeline stops when an agent fails."""
        good_agent = Agent(MockProvider(responses=["OK"]))

        # Create agent that will fail
        class FailingProvider(MockProvider):
            async def complete(self, messages, tools=None, **kwargs):
                raise ValueError("Agent failed!")

        bad_agent = Agent(FailingProvider())

        pipeline = Pipeline(
            [
                ("good", good_agent),
                ("bad", bad_agent),
                ("never_reached", good_agent),
            ]
        )

        result = await pipeline.run("start")

        assert not result.detail.success
        assert len(result.detail.steps) == 2  # Stopped after bad agent
        assert result.detail.steps[1].error is not None

    def test_pipeline_agents_property(self, agent_a, agent_b):
        """Can get list of agents from pipeline."""
        pipeline = Pipeline([("a", agent_a), ("b", agent_b)])

        agents = pipeline.agents
        assert len(agents) == 2
        assert agents[0][0] == "a"
        assert agents[1][0] == "b"


# =============================================================================
# Router Tests
# =============================================================================


class TestRouter:
    """Tests for Router orchestrator."""

    @pytest.mark.asyncio
    async def test_basic_routing(self, agent_a, agent_b):
        """Router routes to correct agent."""
        router = Router(
            agents={"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a" if "route_a" in x else "b",
        )

        result = await router.run("please route_a this")

        assert result.detail.success
        assert len(result.detail.steps) == 1
        assert result.detail.steps[0].agent_id == "a"
        assert result.detail.orchestration_type == "router"

    @pytest.mark.asyncio
    async def test_routing_to_different_agents(self, agent_a, agent_b):
        """Router routes different inputs to different agents."""
        router = Router(
            agents={"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a" if "AAA" in x else "b",
        )

        result1 = await router.run("AAA input")
        result2 = await router.run("BBB input")

        assert result1.detail.steps[0].agent_id == "a"
        assert result2.detail.steps[0].agent_id == "b"

    @pytest.mark.asyncio
    async def test_router_default(self, agent_a, agent_b):
        """Router uses default when route returns unknown agent."""
        router = Router(
            agents={"a": agent_a, "b": agent_b},
            route_fn=lambda x: "unknown",  # Returns invalid agent
            default="a",
        )

        result = await router.run("any input")

        assert result.detail.steps[0].agent_id == "a"

    def test_router_requires_route_fn_or_agent(self, agent_a):
        """Router requires either route_fn or router_agent."""
        with pytest.raises(ValueError):
            Router(agents={"a": agent_a})

    @pytest.mark.asyncio
    async def test_router_with_async_route(self, agent_a, agent_b):
        """Router route method is async and returns (name, metadata)."""
        router = Router(
            agents={"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a",
        )

        name, metadata = await router.route("input")
        assert name == "a"
        assert metadata["method"] == "function"
        assert metadata["selected_agent"] == "a"

    @pytest.mark.asyncio
    async def test_router_with_llm_routing(self, agent_a, agent_b):
        """Router with router_agent uses LLM to pick agent."""
        # LLM-based router that responds with agent name "b"
        router_provider = MockProvider(responses=["b"])
        router_agent = Agent(router_provider, name="router_llm")

        router = Router(
            agents={"a": agent_a, "b": agent_b},
            router_agent=router_agent,
        )

        result = await router.run("some input")

        assert result.detail.success
        assert result.detail.steps[0].agent_id == "b"

    @pytest.mark.asyncio
    async def test_router_llm_fallback_to_default(self, agent_a, agent_b):
        """LLM returns unknown agent name, falls back to default."""
        router_provider = MockProvider(responses=["nonexistent_agent"])
        router_agent = Agent(router_provider, name="router_llm")

        router = Router(
            agents={"a": agent_a, "b": agent_b},
            router_agent=router_agent,
            default="a",
        )

        result = await router.run("some input")

        assert result.detail.success
        assert result.detail.steps[0].agent_id == "a"

    @pytest.mark.asyncio
    async def test_router_agent_error(self, agent_a):
        """Agent raising exception is captured in step."""
        from tantra.exceptions import ProviderError

        # Create an agent that always fails
        class FailingProvider(MockProvider):
            async def complete(self, messages, tools=None, **kwargs):
                raise ProviderError("LLM exploded")

        failing_agent = Agent(FailingProvider(), name="fail")

        router = Router(
            agents={"fail": failing_agent},
            route_fn=lambda x: "fail",
        )

        result = await router.run("trigger error")

        assert not result.detail.success
        assert len(result.detail.steps) == 1
        assert result.detail.steps[0].error is not None


# =============================================================================
# Parallel Tests
# =============================================================================


class TestParallel:
    """Tests for Parallel orchestrator."""

    @pytest.mark.asyncio
    async def test_basic_parallel(self, agent_a, agent_b, agent_c):
        """Parallel runs all agents."""
        parallel = Parallel(
            [
                ("a", agent_a),
                ("b", agent_b),
                ("c", agent_c),
            ]
        )

        result = await parallel.run("input for all")

        assert result.detail.success
        assert len(result.detail.steps) == 3
        assert result.detail.agent_count == 3
        assert result.detail.orchestration_type == "parallel"

    @pytest.mark.asyncio
    async def test_parallel_all_get_same_input(self, agent_a, agent_b):
        """All agents receive the same input."""
        parallel = Parallel([("a", agent_a), ("b", agent_b)])

        result = await parallel.run("shared input")

        assert result.detail.steps[0].input == "shared input"
        assert result.detail.steps[1].input == "shared input"

    @pytest.mark.asyncio
    async def test_parallel_combines_output(self):
        """Parallel combines outputs from all agents."""
        agent1 = Agent(MockProvider(responses=["OUTPUT_1"]))
        agent2 = Agent(MockProvider(responses=["OUTPUT_2"]))

        parallel = Parallel([("a", agent1), ("b", agent2)])
        result = await parallel.run("input")

        # Default combine includes both outputs
        assert "OUTPUT_1" in result.output
        assert "OUTPUT_2" in result.output

    @pytest.mark.asyncio
    async def test_parallel_custom_combine(self):
        """Parallel with custom combine function."""
        agent1 = Agent(MockProvider(responses=["A"]))
        agent2 = Agent(MockProvider(responses=["B"]))

        def custom_combine(steps):
            return " + ".join(s.output for s in steps)

        parallel = Parallel(
            agents=[("a", agent1), ("b", agent2)],
            combine_fn=custom_combine,
        )

        result = await parallel.run("input")

        assert result.output == "A + B"

    @pytest.mark.asyncio
    async def test_parallel_handles_errors(self):
        """Parallel continues even if one agent fails."""
        good_agent = Agent(MockProvider(responses=["OK"]))

        class FailingProvider(MockProvider):
            async def complete(self, messages, tools=None, **kwargs):
                raise ValueError("Failed!")

        bad_agent = Agent(FailingProvider())

        parallel = Parallel(
            [
                ("good1", good_agent),
                ("bad", bad_agent),
                ("good2", good_agent),
            ]
        )

        result = await parallel.run("input")

        assert len(result.detail.steps) == 3
        # One step should have an error
        errors = [s for s in result.detail.steps if s.error]
        assert len(errors) == 1


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_chain(self, agent_a, agent_b):
        """chain() creates a pipeline."""
        pipeline = chain(agent_a, agent_b)

        assert isinstance(pipeline, Pipeline)
        result = await pipeline.run("input")
        assert len(result.detail.steps) == 2

    @pytest.mark.asyncio
    async def test_fan_out(self, agent_a, agent_b, agent_c):
        """fan_out() creates parallel orchestrator."""
        parallel = fan_out(agent_a, agent_b, agent_c)

        assert isinstance(parallel, Parallel)
        result = await parallel.run("input")
        assert len(result.detail.steps) == 3

    @pytest.mark.asyncio
    async def test_select(self, agent_a, agent_b):
        """select() creates router with routing function."""
        router = select(
            {"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a",
        )

        assert isinstance(router, Router)
        result = await router.run("input")
        assert result.detail.steps[0].agent_id == "a"


# =============================================================================
# OrchestrationDetail Tests
# =============================================================================


class TestOrchestrationDetail:
    """Tests for OrchestrationDetail."""

    def test_success_when_no_errors(self):
        """Result is successful when no errors."""
        from tantra.types import RunMetadata

        steps = [
            AgentStep(
                agent_id="a",
                input="in",
                output="out",
                metadata=RunMetadata(
                    run_id=uuid4(),
                    total_tokens=10,
                    prompt_tokens=5,
                    completion_tokens=5,
                    estimated_cost=0.001,
                    duration_ms=100,
                    tool_calls_count=0,
                ),
                duration_ms=100,
            )
        ]

        result = OrchestrationDetail(
            steps=steps,
            orchestration_type="pipeline",
        )

        assert result.success is True

    def test_not_success_when_error(self):
        """Result is not successful when there's an error."""
        from tantra.types import RunMetadata

        steps = [
            AgentStep(
                agent_id="a",
                input="in",
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
                error=ValueError("failed"),
            )
        ]

        result = OrchestrationDetail(
            steps=steps,
            orchestration_type="pipeline",
        )

        assert result.success is False

    def test_agent_count(self):
        """Agent count is unique agents."""
        from tantra.types import RunMetadata

        metadata = RunMetadata(
            run_id=uuid4(),
            total_tokens=10,
            prompt_tokens=5,
            completion_tokens=5,
            estimated_cost=0.001,
            duration_ms=100,
            tool_calls_count=0,
        )

        steps = [
            AgentStep(agent_id="a", input="", output="", metadata=metadata, duration_ms=0),
            AgentStep(agent_id="b", input="", output="", metadata=metadata, duration_ms=0),
            AgentStep(
                agent_id="a", input="", output="", metadata=metadata, duration_ms=0
            ),  # Same as first
        ]

        result = OrchestrationDetail(
            steps=steps,
            orchestration_type="supervisor",
        )

        assert result.agent_count == 2  # Only 'a' and 'b'


# =============================================================================
# Clone Tests
# =============================================================================


class TestClone:
    """Tests for orchestrator clone()."""

    def test_pipeline_clone_returns_new_instance(self, agent_a, agent_b):
        pipeline = Pipeline([("a", agent_a), ("b", agent_b)], name="p")
        cloned = pipeline.clone()
        assert isinstance(cloned, Pipeline)
        assert cloned is not pipeline
        assert cloned.name == "p"

    def test_pipeline_clone_shares_agents(self, agent_a, agent_b):
        pipeline = Pipeline([("a", agent_a), ("b", agent_b)])
        cloned = pipeline.clone()
        assert cloned.agents[0][1] is agent_a
        assert cloned.agents[1][1] is agent_b

    @pytest.mark.asyncio
    async def test_pipeline_clone_is_functional(self):
        a = Agent(MockProvider(responses=["A"]))
        b = Agent(MockProvider(responses=["B"]))
        pipeline = Pipeline([("a", a), ("b", b)])
        cloned = pipeline.clone()
        result = await cloned.run("input")
        assert result.output == "B"
        assert result.detail.success

    def test_router_clone_returns_new_instance(self, agent_a, agent_b):
        router = Router(
            agents={"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a",
            name="r",
        )
        cloned = router.clone()
        assert isinstance(cloned, Router)
        assert cloned is not router
        assert cloned.name == "r"

    def test_router_clone_preserves_routing(self, agent_a, agent_b):
        def fn(x):
            return "b"

        router = Router(agents={"a": agent_a, "b": agent_b}, route_fn=fn, default="a")
        cloned = router.clone()
        assert cloned.route_fn is fn
        assert cloned.default == "a"

    @pytest.mark.asyncio
    async def test_router_clone_is_functional(self):
        a = Agent(MockProvider(responses=["A"]))
        b = Agent(MockProvider(responses=["B"]))
        router = Router(agents={"a": a, "b": b}, route_fn=lambda x: "b")
        cloned = router.clone()
        result = await cloned.run("input")
        assert result.detail.steps[0].agent_id == "b"

    def test_parallel_clone_returns_new_instance(self, agent_a, agent_b):
        parallel = Parallel([("a", agent_a), ("b", agent_b)], name="par")
        cloned = parallel.clone()
        assert isinstance(cloned, Parallel)
        assert cloned is not parallel
        assert cloned.name == "par"

    @pytest.mark.asyncio
    async def test_parallel_clone_is_functional(self):
        a = Agent(MockProvider(responses=["A"]))
        b = Agent(MockProvider(responses=["B"]))
        parallel = Parallel([("a", a), ("b", b)])
        cloned = parallel.clone()
        result = await cloned.run("input")
        assert result.detail.success
        assert len(result.detail.steps) == 2
