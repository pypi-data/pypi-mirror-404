"""Tests for lifecycle hooks."""

import logging
from uuid import UUID

import pytest
from conftest import MockProvider

from tantra import Agent, RunHooks, RunResult, ToolSet, tool
from tantra.context import RunContext
from tantra.hooks import _invoke_hooks
from tantra.types import ProviderResponse, ToolCallData

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class RecordingHook(RunHooks):
    """Hook that records all calls for test assertions."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def on_run_start(self, *, run_id, user_input, name, context):
        self.calls.append(
            (
                "on_run_start",
                {
                    "run_id": run_id,
                    "user_input": user_input,
                    "name": name,
                    "context": context,
                },
            )
        )

    async def on_run_end(self, *, run_id, result, context):
        self.calls.append(("on_run_end", {"run_id": run_id, "result": result, "context": context}))

    async def on_run_error(self, *, run_id, error, context):
        self.calls.append(("on_run_error", {"run_id": run_id, "error": error, "context": context}))

    async def on_tool_call(self, *, run_id, tool_name, arguments, context):
        self.calls.append(
            (
                "on_tool_call",
                {
                    "run_id": run_id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "context": context,
                },
            )
        )

    async def on_tool_result(self, *, run_id, tool_name, result, duration_ms, context):
        self.calls.append(
            (
                "on_tool_result",
                {
                    "run_id": run_id,
                    "tool_name": tool_name,
                    "result": result,
                    "duration_ms": duration_ms,
                    "context": context,
                },
            )
        )

    async def on_orchestration_start(self, *, run_id, user_input, orchestration_type, context):
        self.calls.append(
            (
                "on_orchestration_start",
                {
                    "run_id": run_id,
                    "user_input": user_input,
                    "orchestration_type": orchestration_type,
                    "context": context,
                },
            )
        )

    async def on_orchestration_end(self, *, run_id, result, orchestration_type, context):
        self.calls.append(
            (
                "on_orchestration_end",
                {
                    "run_id": run_id,
                    "result": result,
                    "orchestration_type": orchestration_type,
                    "context": context,
                },
            )
        )

    async def on_orchestration_error(self, *, run_id, error, orchestration_type, context):
        self.calls.append(
            (
                "on_orchestration_error",
                {
                    "run_id": run_id,
                    "error": error,
                    "orchestration_type": orchestration_type,
                    "context": context,
                },
            )
        )

    def names(self) -> list[str]:
        """Return list of hook method names that were called."""
        return [name for name, _ in self.calls]


class FailingHook(RunHooks):
    """Hook that raises on every method."""

    async def on_run_start(self, **kwargs):
        raise RuntimeError("hook failed")

    async def on_run_end(self, **kwargs):
        raise RuntimeError("hook failed")

    async def on_run_error(self, **kwargs):
        raise RuntimeError("hook failed")

    async def on_tool_call(self, **kwargs):
        raise RuntimeError("hook failed")

    async def on_tool_result(self, **kwargs):
        raise RuntimeError("hook failed")


def _tool_call_response(tool_name, arguments, call_id="call-1"):
    return ProviderResponse(
        content=None,
        tool_calls=[ToolCallData(id=call_id, name=tool_name, arguments=arguments)],
        prompt_tokens=10,
        completion_tokens=5,
    )


def _text_response(text):
    return ProviderResponse(
        content=text,
        tool_calls=None,
        prompt_tokens=10,
        completion_tokens=5,
    )


def _make_tools():
    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city."""
        return f"Sunny in {city}"

    return ToolSet([get_weather])


# ---------------------------------------------------------------------------
# Tests: RunHooks base class
# ---------------------------------------------------------------------------


class TestRunHooksBase:
    """Tests for RunHooks base class."""

    @pytest.mark.asyncio
    async def test_default_methods_are_noop(self):
        """All default methods execute without error."""
        hooks = RunHooks()
        ctx = RunContext()
        from uuid import uuid4

        rid = uuid4()
        await hooks.on_run_start(run_id=rid, user_input="hi", name=None, context=ctx)
        await hooks.on_run_end(run_id=rid, result=None, context=ctx)
        await hooks.on_run_error(run_id=rid, error=Exception("x"), context=ctx)
        await hooks.on_tool_call(run_id=rid, tool_name="t", arguments={}, context=ctx)
        await hooks.on_tool_result(
            run_id=rid, tool_name="t", result="ok", duration_ms=1.0, context=ctx
        )

    @pytest.mark.asyncio
    async def test_subclass_partial_override(self):
        """Subclass can override only some methods."""

        class PartialHook(RunHooks):
            async def on_run_start(self, **kwargs):
                pass  # only override this one

        hook = PartialHook()
        ctx = RunContext()
        from uuid import uuid4

        rid = uuid4()
        # Non-overridden methods should still work
        await hook.on_run_end(run_id=rid, result=None, context=ctx)
        await hook.on_tool_call(run_id=rid, tool_name="t", arguments={}, context=ctx)


# ---------------------------------------------------------------------------
# Tests: _invoke_hooks helper
# ---------------------------------------------------------------------------


class TestInvokeHooks:
    """Tests for the _invoke_hooks helper function."""

    @pytest.mark.asyncio
    async def test_calls_all_hooks_in_order(self):
        """All hooks are called in order."""
        hook1 = RecordingHook()
        hook2 = RecordingHook()
        ctx = RunContext()
        from uuid import uuid4

        rid = uuid4()
        await _invoke_hooks(
            [hook1, hook2],
            "on_run_start",
            run_id=rid,
            user_input="hi",
            name=None,
            context=ctx,
        )
        assert len(hook1.calls) == 1
        assert len(hook2.calls) == 1
        assert hook1.calls[0][0] == "on_run_start"
        assert hook2.calls[0][0] == "on_run_start"

    @pytest.mark.asyncio
    async def test_hook_error_does_not_crash(self):
        """If one hook raises, the rest still run."""
        failing = FailingHook()
        recorder = RecordingHook()
        ctx = RunContext()
        from uuid import uuid4

        rid = uuid4()
        # FailingHook first, RecordingHook second
        await _invoke_hooks(
            [failing, recorder],
            "on_run_start",
            run_id=rid,
            user_input="hi",
            name=None,
            context=ctx,
        )
        # RecordingHook should still have been called
        assert len(recorder.calls) == 1

    @pytest.mark.asyncio
    async def test_hook_error_is_logged(self, caplog):
        """Hook exceptions are logged."""
        failing = FailingHook()
        ctx = RunContext()
        from uuid import uuid4

        rid = uuid4()
        with caplog.at_level(logging.ERROR, logger="tantra.hooks"):
            await _invoke_hooks(
                [failing],
                "on_run_start",
                run_id=rid,
                user_input="hi",
                name=None,
                context=ctx,
            )
        assert "FailingHook.on_run_start() failed" in caplog.text

    @pytest.mark.asyncio
    async def test_empty_hooks_list_is_safe(self):
        """Empty hooks list doesn't error."""
        ctx = RunContext()
        from uuid import uuid4

        rid = uuid4()
        await _invoke_hooks([], "on_run_start", run_id=rid, user_input="hi", name=None, context=ctx)


# ---------------------------------------------------------------------------
# Tests: Run-level hooks
# ---------------------------------------------------------------------------


class TestRunLevelHooks:
    """Tests for on_run_start, on_run_end, on_run_error."""

    @pytest.mark.asyncio
    async def test_on_run_start_called(self):
        """on_run_start is called with correct arguments."""
        hook = RecordingHook()
        provider = MockProvider(responses=["Hello!"])
        agent = Agent(provider, system_prompt="hi", name="test-agent", hooks=[hook])

        await agent.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_run_start"]
        assert len(start_calls) == 1
        _, data = start_calls[0]
        assert data["user_input"] == "Hello"
        assert data["name"] == "test-agent"
        assert isinstance(data["run_id"], UUID)
        assert isinstance(data["context"], RunContext)

    @pytest.mark.asyncio
    async def test_on_run_end_called(self):
        """on_run_end is called with RunResult."""
        hook = RecordingHook()
        provider = MockProvider(responses=["World!"])
        agent = Agent(provider, hooks=[hook])

        await agent.run("Hello")

        end_calls = [(n, d) for n, d in hook.calls if n == "on_run_end"]
        assert len(end_calls) == 1
        _, data = end_calls[0]
        assert isinstance(data["result"], RunResult)
        assert data["result"].output == "World!"
        assert isinstance(data["context"], RunContext)

    @pytest.mark.asyncio
    async def test_on_run_error_called_on_exception(self):
        """on_run_error fires when engine raises."""
        hook = RecordingHook()

        @tool
        def loop_tool() -> str:
            """A tool."""
            return "again"

        tools = ToolSet([loop_tool])
        provider = MockProvider(responses=[_tool_call_response("loop_tool", {})] * 5)
        agent = Agent(provider, tools=tools, max_iterations=2, hooks=[hook])

        with pytest.raises(Exception):
            await agent.run("Go")

        error_calls = [(n, d) for n, d in hook.calls if n == "on_run_error"]
        assert len(error_calls) == 1
        assert isinstance(error_calls[0][1]["error"], Exception)

    @pytest.mark.asyncio
    async def test_on_run_end_not_called_on_error(self):
        """on_run_end does NOT fire when the run errors."""
        hook = RecordingHook()

        @tool
        def loop_tool() -> str:
            """A tool."""
            return "again"

        tools = ToolSet([loop_tool])
        provider = MockProvider(responses=[_tool_call_response("loop_tool", {})] * 5)
        agent = Agent(provider, tools=tools, max_iterations=2, hooks=[hook])

        with pytest.raises(Exception):
            await agent.run("Go")

        end_calls = [n for n, _ in hook.calls if n == "on_run_end"]
        assert len(end_calls) == 0

    @pytest.mark.asyncio
    async def test_hooks_not_called_for_rule_match(self):
        """Hooks do not fire when rules match (no LLM call)."""
        from tantra.rules import KeywordRule

        hook = RecordingHook()
        provider = MockProvider(responses=["Never called"])
        agent = Agent(
            provider,
            rules=[KeywordRule(keywords=["hello"], response="Hi from rule")],
            hooks=[hook],
        )

        result = await agent.run("hello")
        assert result.output == "Hi from rule"
        assert len(hook.calls) == 0

    @pytest.mark.asyncio
    async def test_multiple_hooks_all_called(self):
        """Multiple hooks all receive events."""
        hook1 = RecordingHook()
        hook2 = RecordingHook()
        provider = MockProvider(responses=["OK"])
        agent = Agent(provider, hooks=[hook1, hook2])

        await agent.run("Test")

        assert "on_run_start" in hook1.names()
        assert "on_run_start" in hook2.names()
        assert "on_run_end" in hook1.names()
        assert "on_run_end" in hook2.names()

    @pytest.mark.asyncio
    async def test_hooks_with_name(self):
        """name is passed to hooks."""
        hook = RecordingHook()
        provider = MockProvider(responses=["OK"])
        agent = Agent(provider, name="my-agent", hooks=[hook])

        await agent.run("Test")

        start_data = hook.calls[0][1]
        assert start_data["name"] == "my-agent"

    @pytest.mark.asyncio
    async def test_hook_error_does_not_crash_run(self):
        """A failing hook doesn't crash the agent run."""
        failing = FailingHook()
        provider = MockProvider(responses=["Still works"])
        agent = Agent(provider, hooks=[failing])

        result = await agent.run("Test")
        assert result.output == "Still works"


# ---------------------------------------------------------------------------
# Tests: Tool-level hooks
# ---------------------------------------------------------------------------


class TestToolLevelHooks:
    """Tests for on_tool_call and on_tool_result."""

    @pytest.mark.asyncio
    async def test_on_tool_call_fired(self):
        """on_tool_call fires with correct tool_name and arguments."""
        hook = RecordingHook()
        tools = _make_tools()
        provider = MockProvider(
            responses=[
                _tool_call_response("get_weather", {"city": "Tokyo"}),
                _text_response("Sunny in Tokyo!"),
            ]
        )
        agent = Agent(provider, tools=tools, hooks=[hook])

        await agent.run("Weather?")

        tool_calls = [(n, d) for n, d in hook.calls if n == "on_tool_call"]
        assert len(tool_calls) == 1
        _, data = tool_calls[0]
        assert data["tool_name"] == "get_weather"
        assert data["arguments"] == {"city": "Tokyo"}

    @pytest.mark.asyncio
    async def test_on_tool_result_fired(self):
        """on_tool_result fires with result and duration."""
        hook = RecordingHook()
        tools = _make_tools()
        provider = MockProvider(
            responses=[
                _tool_call_response("get_weather", {"city": "NYC"}),
                _text_response("Done"),
            ]
        )
        agent = Agent(provider, tools=tools, hooks=[hook])

        await agent.run("Weather?")

        results = [(n, d) for n, d in hook.calls if n == "on_tool_result"]
        assert len(results) == 1
        _, data = results[0]
        assert data["tool_name"] == "get_weather"
        assert "Sunny in NYC" in data["result"]
        assert data["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_tool_hooks_with_parallel_execution(self):
        """Tool hooks fire for each tool in parallel execution."""
        hook = RecordingHook()

        @tool
        def tool_a(x: str) -> str:
            """Tool A."""
            return f"A:{x}"

        @tool
        def tool_b(y: str) -> str:
            """Tool B."""
            return f"B:{y}"

        tools = ToolSet([tool_a, tool_b])
        provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[
                        ToolCallData(id="c1", name="tool_a", arguments={"x": "1"}),
                        ToolCallData(id="c2", name="tool_b", arguments={"y": "2"}),
                    ],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                _text_response("Done"),
            ]
        )
        agent = Agent(provider, tools=tools, hooks=[hook])

        await agent.run("Call both")

        tool_call_names = [d["tool_name"] for n, d in hook.calls if n == "on_tool_call"]
        tool_result_names = [d["tool_name"] for n, d in hook.calls if n == "on_tool_result"]
        assert "tool_a" in tool_call_names
        assert "tool_b" in tool_call_names
        assert "tool_a" in tool_result_names
        assert "tool_b" in tool_result_names

    @pytest.mark.asyncio
    async def test_tool_hooks_with_sequential_execution(self):
        """Tool hooks fire in sequential execution mode."""
        hook = RecordingHook()
        tools = _make_tools()
        provider = MockProvider(
            responses=[
                _tool_call_response("get_weather", {"city": "LA"}),
                _text_response("Done"),
            ]
        )
        agent = Agent(
            provider,
            tools=tools,
            hooks=[hook],
            parallel_tool_execution=False,
        )

        await agent.run("Weather?")

        tool_calls = [n for n, _ in hook.calls if n == "on_tool_call"]
        tool_results = [n for n, _ in hook.calls if n == "on_tool_result"]
        assert len(tool_calls) == 1
        assert len(tool_results) == 1


# ---------------------------------------------------------------------------
# Tests: Context injection via hooks
# ---------------------------------------------------------------------------


class TestContextInjection:
    """Tests for hooks injecting data into RunContext for tools."""

    @pytest.mark.asyncio
    async def test_hook_writes_to_context_tool_reads(self):
        """Hook injects data via RunContext, tool reads it."""

        class SetupHook(RunHooks):
            async def on_run_start(self, *, run_id, user_input, name, context):
                context.set("injected_key", "injected_value")

        @tool
        def read_context(context: RunContext) -> str:
            """Read from context."""
            return context.get("injected_key", "missing")

        tools = ToolSet([read_context])
        hook = SetupHook()
        provider = MockProvider(
            responses=[
                _tool_call_response("read_context", {}),
                _text_response("Done"),
            ]
        )
        agent = Agent(provider, tools=tools, hooks=[hook])

        result = await agent.run("Read it")

        # The tool should have read the value set by the hook
        assert result.context.get("injected_key") == "injected_value"

    @pytest.mark.asyncio
    async def test_on_run_end_receives_context(self):
        """on_run_end receives the same RunContext used during the run."""
        hook = RecordingHook()
        provider = MockProvider(responses=["OK"])
        agent = Agent(provider, hooks=[hook])

        result = await agent.run("Test")

        end_calls = [(n, d) for n, d in hook.calls if n == "on_run_end"]
        assert len(end_calls) == 1
        assert end_calls[0][1]["context"] is result.context


# ---------------------------------------------------------------------------
# Tests: Builder methods
# ---------------------------------------------------------------------------


class TestBuilderMethods:
    """Tests for with_hooks() and clone()."""

    def test_with_hooks_creates_new_agent(self):
        """with_hooks returns a new agent with the specified hooks."""
        provider = MockProvider()
        hook = RecordingHook()
        agent = Agent(provider)

        new_agent = agent.with_hooks([hook])

        assert new_agent is not agent
        assert len(new_agent.hooks) == 1
        assert new_agent.hooks[0] is hook
        assert len(agent.hooks) == 0

    def test_clone_shares_hooks(self):
        """Cloned agent shares the same hooks list."""
        hook = RecordingHook()
        provider = MockProvider()
        agent = Agent(provider, hooks=[hook])

        cloned = agent.clone()

        assert len(cloned.hooks) == 1
        assert cloned.hooks[0] is hook

    def test_with_tools_preserves_hooks(self):
        """with_tools() preserves existing hooks."""
        hook = RecordingHook()
        provider = MockProvider()
        agent = Agent(provider, hooks=[hook])

        new_agent = agent.with_tools(ToolSet([]))

        assert len(new_agent.hooks) == 1
        assert new_agent.hooks[0] is hook

    def test_with_system_prompt_preserves_hooks(self):
        """with_system_prompt() preserves existing hooks."""
        hook = RecordingHook()
        provider = MockProvider()
        agent = Agent(provider, hooks=[hook])

        new_agent = agent.with_system_prompt("new prompt")

        assert len(new_agent.hooks) == 1
        assert new_agent.hooks[0] is hook

    def test_with_parallel_tool_execution_preserves_hooks(self):
        """with_parallel_tool_execution() preserves existing hooks."""
        hook = RecordingHook()
        provider = MockProvider()
        agent = Agent(provider, hooks=[hook])

        new_agent = agent.with_parallel_tool_execution(False)

        assert len(new_agent.hooks) == 1
        assert new_agent.hooks[0] is hook

    def test_hooks_property(self):
        """hooks property returns the hooks list."""
        hook = RecordingHook()
        provider = MockProvider()
        agent = Agent(provider, hooks=[hook])

        assert agent.hooks == [hook]

    def test_no_hooks_by_default(self):
        """Agent has empty hooks list by default."""
        provider = MockProvider()
        agent = Agent(provider)

        assert agent.hooks == []


# ---------------------------------------------------------------------------
# Tests: Orchestration hooks
# ---------------------------------------------------------------------------


def _make_agent(responses=None, name=None):
    """Create a simple agent with MockProvider."""
    provider = MockProvider(responses=responses or ["OK"])
    return Agent(provider, system_prompt="Test", name=name or "test")


class TestPipelineHooks:
    """Tests for Pipeline orchestration hooks."""

    @pytest.mark.asyncio
    async def test_on_orchestration_start_and_end(self):
        """Pipeline fires on_orchestration_start and on_orchestration_end."""
        from tantra.orchestration import Pipeline

        hook = RecordingHook()
        pipeline = Pipeline(
            agents=[("a", _make_agent()), ("b", _make_agent())],
            hooks=[hook],
        )

        result = await pipeline.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        end_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_end"]
        assert len(start_calls) == 1
        assert len(end_calls) == 1
        assert start_calls[0][1]["user_input"] == "Hello"
        assert start_calls[0][1]["orchestration_type"] == "pipeline"
        assert isinstance(start_calls[0][1]["run_id"], UUID)
        assert end_calls[0][1]["orchestration_type"] == "pipeline"
        assert end_calls[0][1]["result"] is result

    @pytest.mark.asyncio
    async def test_no_hooks_zero_overhead(self):
        """Pipeline with no hooks runs without error."""
        from tantra.orchestration import Pipeline

        pipeline = Pipeline(agents=[("a", _make_agent())])
        result = await pipeline.run("Hello")
        assert result.output == "OK"

    @pytest.mark.asyncio
    async def test_multiple_hooks(self):
        """Multiple hooks all receive orchestration events."""
        from tantra.orchestration import Pipeline

        hook1 = RecordingHook()
        hook2 = RecordingHook()
        pipeline = Pipeline(
            agents=[("a", _make_agent())],
            hooks=[hook1, hook2],
        )

        await pipeline.run("Hello")

        assert "on_orchestration_start" in hook1.names()
        assert "on_orchestration_start" in hook2.names()
        assert "on_orchestration_end" in hook1.names()
        assert "on_orchestration_end" in hook2.names()

    @pytest.mark.asyncio
    async def test_hook_error_does_not_crash_pipeline(self):
        """Failing hooks don't crash the pipeline."""
        from tantra.orchestration import Pipeline

        pipeline = Pipeline(
            agents=[("a", _make_agent())],
            hooks=[FailingHook()],
        )

        result = await pipeline.run("Hello")
        assert result.output == "OK"


class TestRouterHooks:
    """Tests for Router orchestration hooks."""

    @pytest.mark.asyncio
    async def test_on_orchestration_start_and_end(self):
        """Router fires on_orchestration_start and on_orchestration_end."""
        from tantra.orchestration import Router

        hook = RecordingHook()
        router = Router(
            agents={"main": _make_agent()},
            route_fn=lambda x: "main",
            hooks=[hook],
        )

        result = await router.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        end_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_end"]
        assert len(start_calls) == 1
        assert len(end_calls) == 1
        assert start_calls[0][1]["orchestration_type"] == "router"
        assert end_calls[0][1]["result"] is result


class TestParallelHooks:
    """Tests for Parallel orchestration hooks."""

    @pytest.mark.asyncio
    async def test_on_orchestration_start_and_end(self):
        """Parallel fires on_orchestration_start and on_orchestration_end."""
        from tantra.orchestration import Parallel

        hook = RecordingHook()
        parallel = Parallel(
            agents=[("a", _make_agent()), ("b", _make_agent())],
            hooks=[hook],
        )

        result = await parallel.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        end_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_end"]
        assert len(start_calls) == 1
        assert len(end_calls) == 1
        assert start_calls[0][1]["orchestration_type"] == "parallel"
        assert end_calls[0][1]["result"] is result


class TestGraphHooks:
    """Tests for Graph orchestration hooks."""

    @pytest.mark.asyncio
    async def test_on_orchestration_start_and_end(self):
        """Graph fires on_orchestration_start and on_orchestration_end."""
        from tantra.orchestration import AgentNode, Graph

        hook = RecordingHook()
        graph = Graph(name="test-graph", hooks=[hook])
        graph.add_node(AgentNode(id="a", agent=_make_agent()))
        graph.add_edge("START", "a")
        graph.set_finish_point("a")

        result = await graph.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        end_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_end"]
        assert len(start_calls) == 1
        assert len(end_calls) == 1
        assert start_calls[0][1]["orchestration_type"] == "graph"
        assert start_calls[0][1]["user_input"] == "Hello"
        assert end_calls[0][1]["result"] is result


class TestSwarmHooks:
    """Tests for Swarm orchestration hooks."""

    @pytest.mark.asyncio
    async def test_on_orchestration_start_and_end(self):
        """Swarm fires on_orchestration_start and on_orchestration_end."""
        from tantra.orchestration import Swarm

        hook = RecordingHook()
        # Single agent, no handoffs -> completes immediately
        swarm = Swarm(
            agents={"triage": _make_agent(name="triage")},
            handoffs={"triage": []},
            entry_point="triage",
            hooks=[hook],
        )

        result = await swarm.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        end_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_end"]
        assert len(start_calls) == 1
        assert len(end_calls) == 1
        assert start_calls[0][1]["orchestration_type"] == "swarm"
        assert end_calls[0][1]["result"] is result


class TestOrchestrationHooksContext:
    """Tests for context passing in orchestration hooks."""

    @pytest.mark.asyncio
    async def test_shared_context_passed_to_hooks(self):
        """Shared context is passed to orchestration hooks."""
        from tantra.orchestration import Pipeline

        hook = RecordingHook()
        ctx = RunContext({"key": "value"})
        pipeline = Pipeline(
            agents=[("a", _make_agent())],
            hooks=[hook],
        )

        await pipeline.run("Hello", shared_context=ctx)

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        assert start_calls[0][1]["context"] is ctx

    @pytest.mark.asyncio
    async def test_none_context_when_not_provided(self):
        """Context is None when no shared_context or session_id."""
        from tantra.orchestration import Pipeline

        hook = RecordingHook()
        pipeline = Pipeline(
            agents=[("a", _make_agent())],
            hooks=[hook],
        )

        await pipeline.run("Hello")

        start_calls = [(n, d) for n, d in hook.calls if n == "on_orchestration_start"]
        assert start_calls[0][1]["context"] is None
