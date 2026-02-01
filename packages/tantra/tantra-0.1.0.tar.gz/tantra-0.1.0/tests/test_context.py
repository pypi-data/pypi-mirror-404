"""Tests for RunContext shared execution context."""

import pytest
from conftest import MockProvider

from tantra import Agent, RunContext, ToolSet, tool
from tantra.context import MemoryContextStore
from tantra.types import ProviderResponse, ToolCallData

# =============================================================================
# RunContext unit tests
# =============================================================================


class TestRunContext:
    def test_empty_context(self):
        ctx = RunContext()
        assert ctx.get("key") is None
        assert ctx.get("key", "default") == "default"

    def test_init_from_dict(self):
        ctx = RunContext({"a": 1, "b": "hello"})
        assert ctx.get("a") == 1
        assert ctx.get("b") == "hello"

    def test_set_and_get(self):
        ctx = RunContext()
        ctx.set("key", 42)
        assert ctx.get("key") == 42

    def test_overwrite(self):
        ctx = RunContext({"key": "old"})
        ctx.set("key", "new")
        assert ctx.get("key") == "new"

    def test_contains(self):
        ctx = RunContext({"exists": True})
        assert "exists" in ctx
        assert "missing" not in ctx

    def test_to_dict(self):
        ctx = RunContext({"a": 1})
        ctx.set("b", 2)
        d = ctx.to_dict()
        assert d == {"a": 1, "b": 2}
        # Verify shallow copy — modifying returned dict doesn't affect context
        d["c"] = 3
        assert "c" not in ctx

    def test_clear(self):
        ctx = RunContext({"a": 1, "b": 2})
        ctx.clear()
        assert ctx.get("a") is None
        assert ctx.to_dict() == {}

    def test_repr(self):
        ctx = RunContext({"key": "val"})
        assert "key" in repr(ctx)
        assert "val" in repr(ctx)

    def test_complex_values(self):
        ctx = RunContext()
        ctx.set("list", [1, 2, 3])
        ctx.set("dict", {"nested": True})
        ctx.set("none", None)
        assert ctx.get("list") == [1, 2, 3]
        assert ctx.get("dict") == {"nested": True}
        assert ctx.get("none") is None
        assert "none" in ctx


# =============================================================================
# ContextStore tests
# =============================================================================


class TestMemoryContextStore:
    @pytest.mark.asyncio
    async def test_save_and_load(self):
        store = MemoryContextStore()
        await store.save("sess1", {"key": "value"})
        data = await store.load("sess1")
        assert data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_load_nonexistent(self):
        store = MemoryContextStore()
        data = await store.load("nonexistent")
        assert data == {}

    @pytest.mark.asyncio
    async def test_overwrite_session(self):
        store = MemoryContextStore()
        await store.save("sess1", {"v": 1})
        await store.save("sess1", {"v": 2})
        data = await store.load("sess1")
        assert data == {"v": 2}

    @pytest.mark.asyncio
    async def test_separate_sessions(self):
        store = MemoryContextStore()
        await store.save("a", {"from": "a"})
        await store.save("b", {"from": "b"})
        assert (await store.load("a")) == {"from": "a"}
        assert (await store.load("b")) == {"from": "b"}

    @pytest.mark.asyncio
    async def test_save_returns_copy(self):
        """Modifying loaded data doesn't affect stored data."""
        store = MemoryContextStore()
        await store.save("sess1", {"key": "val"})
        loaded = await store.load("sess1")
        loaded["extra"] = "modified"
        reloaded = await store.load("sess1")
        assert "extra" not in reloaded


# =============================================================================
# Tool context detection tests
# =============================================================================


class TestToolContextDetection:
    def test_tool_without_context(self):
        @tool
        def plain(x: str) -> str:
            """Plain tool."""
            return x

        assert not plain.accepts_context

    def test_tool_with_context(self):
        @tool
        def ctx_tool(x: str, context: RunContext) -> str:
            """Tool with context."""
            return x

        assert ctx_tool.accepts_context

    def test_context_excluded_from_schema(self):
        @tool
        def ctx_tool(x: str, context: RunContext) -> str:
            """Do something.

            Args:
                x: The input.
            """
            return x

        schema = ctx_tool.get_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "x" in props
        assert "context" not in props

    def test_context_str_not_detected(self):
        """A context: str parameter is a normal LLM parameter, not RunContext."""

        @tool
        def normal_tool(context: str) -> str:
            """Tool with context string param."""
            return context

        assert not normal_tool.accepts_context
        schema = normal_tool.get_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "context" in props  # Exposed to LLM

    def test_context_not_required_in_schema(self):
        @tool
        def ctx_tool(x: str, context: RunContext) -> str:
            """Tool."""
            return x

        schema = ctx_tool.get_schema()
        required = schema["function"]["parameters"]["required"]
        assert "x" in required
        assert "context" not in required


# =============================================================================
# Tool context injection tests
# =============================================================================


class TestToolContextInjection:
    @pytest.mark.asyncio
    async def test_context_injected(self):
        received = {}

        @tool
        def capture(x: str, context: RunContext) -> str:
            """Capture context."""
            received["ctx"] = context
            return context.get("greeting", "none")

        ctx = RunContext({"greeting": "hello"})
        result = await capture.execute(context=ctx, x="test")
        assert result == "hello"
        assert received["ctx"] is ctx

    @pytest.mark.asyncio
    async def test_context_not_injected_when_not_accepted(self):
        @tool
        def plain(x: str) -> str:
            """Plain tool."""
            return x

        # Should work fine — context is silently ignored
        result = await plain.execute(context=RunContext(), x="test")
        assert result == "test"

    @pytest.mark.asyncio
    async def test_tool_writes_to_context(self):
        @tool
        def writer(context: RunContext) -> str:
            """Write to context."""
            context.set("written", True)
            return "done"

        ctx = RunContext()
        await writer.execute(context=ctx)
        assert ctx.get("written") is True

    @pytest.mark.asyncio
    async def test_tools_share_context(self):
        @tool
        def tool_a(context: RunContext) -> str:
            """Tool A writes."""
            context.set("from_a", "hello")
            return "a done"

        @tool
        def tool_b(context: RunContext) -> str:
            """Tool B reads."""
            return f"a said: {context.get('from_a', 'nothing')}"

        ctx = RunContext()
        await tool_a.execute(context=ctx)
        result = await tool_b.execute(context=ctx)
        assert result == "a said: hello"


# =============================================================================
# ToolSet context tests
# =============================================================================


class TestToolSetContext:
    @pytest.mark.asyncio
    async def test_toolset_passes_context(self):
        captured = {}

        @tool
        def my_tool(x: str, context: RunContext) -> str:
            """Tool."""
            captured["val"] = context.get("key")
            return "ok"

        ts = ToolSet([my_tool])
        ctx = RunContext({"key": "value"})
        await ts.execute("my_tool", {"x": "test"}, context=ctx)
        assert captured["val"] == "value"


# =============================================================================
# Agent integration tests
# =============================================================================


class TestAgentRunContext:
    @pytest.mark.asyncio
    async def test_context_on_result(self):
        """RunResult includes the RunContext from the run."""
        provider = MockProvider(responses=["Hello!"])
        agent = Agent(provider)
        result = await agent.run("Hi")
        assert result.context is not None
        assert isinstance(result.context, RunContext)

    @pytest.mark.asyncio
    async def test_context_available_to_tools(self):
        """Tools receive RunContext during agent execution."""
        captured = {}

        @tool
        def check_ctx(context: RunContext) -> str:
            """Check context."""
            captured["received"] = True
            return "checked"

        tools = ToolSet([check_ctx])
        tool_call = ToolCallData(id="c1", name="check_ctx", arguments={})
        provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None, tool_calls=[tool_call], prompt_tokens=10, completion_tokens=5
                ),
                ProviderResponse(
                    content="Done", tool_calls=None, prompt_tokens=10, completion_tokens=5
                ),
            ]
        )

        agent = Agent(provider, tools=tools)
        result = await agent.run("check")
        assert result.output == "Done"
        assert captured["received"] is True

    @pytest.mark.asyncio
    async def test_context_survives_multiple_tool_calls(self):
        """Context persists across tool calls within a single run."""

        @tool
        def step1(context: RunContext) -> str:
            """Step 1."""
            context.set("step1_done", True)
            return "step1 complete"

        @tool
        def step2(context: RunContext) -> str:
            """Step 2."""
            return f"step1 was done: {context.get('step1_done', False)}"

        tools = ToolSet([step1, step2])
        provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[ToolCallData(id="c1", name="step1", arguments={})],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content=None,
                    tool_calls=[ToolCallData(id="c2", name="step2", arguments={})],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content="All done",
                    tool_calls=None,
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
            ]
        )

        agent = Agent(provider, tools=tools)
        result = await agent.run("do steps")
        assert result.output == "All done"
        assert result.context.get("step1_done") is True

    @pytest.mark.asyncio
    async def test_fresh_context_per_run(self):
        """Each run gets a fresh context."""
        captured_values = []

        @tool
        def track(context: RunContext) -> str:
            """Track context state."""
            val = context.get("counter", 0)
            captured_values.append(val)
            context.set("counter", val + 1)
            return "tracked"

        tools = ToolSet([track])

        def make_provider():
            return MockProvider(
                responses=[
                    ProviderResponse(
                        content=None,
                        tool_calls=[ToolCallData(id="c1", name="track", arguments={})],
                        prompt_tokens=10,
                        completion_tokens=5,
                    ),
                    ProviderResponse(
                        content="ok", tool_calls=None, prompt_tokens=10, completion_tokens=5
                    ),
                ]
            )

        # Two separate runs without session_id — each starts fresh
        agent = Agent(make_provider(), tools=tools)
        await agent.run("run1")
        agent._engine.provider = make_provider()
        agent._engine.provider._call_index = 0
        # Reset provider for second run
        agent2 = Agent(make_provider(), tools=tools)
        await agent2.run("run2")

        # Both should start with counter=0
        assert captured_values == [0, 0]

    @pytest.mark.asyncio
    async def test_session_persistence(self):
        """Context persists across runs with the same session_id."""
        values_seen = []

        @tool
        def accumulate(context: RunContext) -> str:
            """Accumulate."""
            val = context.get("counter", 0)
            values_seen.append(val)
            context.set("counter", val + 1)
            return f"counter={val}"

        tools = ToolSet([accumulate])

        def make_responses():
            return [
                ProviderResponse(
                    content=None,
                    tool_calls=[ToolCallData(id="c1", name="accumulate", arguments={})],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content="ok", tool_calls=None, prompt_tokens=10, completion_tokens=5
                ),
            ]

        store = MemoryContextStore()
        agent = Agent(
            MockProvider(responses=make_responses()),
            tools=tools,
            context_store=store,
        )

        await agent.run("run1", session_id="sess_1")

        # Create new agent with same store to simulate separate request
        agent2 = Agent(
            MockProvider(responses=make_responses()),
            tools=tools,
            context_store=store,
        )
        await agent2.run("run2", session_id="sess_1")

        # First run starts at 0, second run starts at 1 (loaded from store)
        assert values_seen == [0, 1]

    @pytest.mark.asyncio
    async def test_different_sessions_isolated(self):
        """Different session_ids have isolated contexts."""
        values_seen = []

        @tool
        def check(context: RunContext) -> str:
            """Check."""
            values_seen.append(context.get("counter", 0))
            context.set("counter", 99)
            return "ok"

        tools = ToolSet([check])

        def make_responses():
            return [
                ProviderResponse(
                    content=None,
                    tool_calls=[ToolCallData(id="c1", name="check", arguments={})],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content="ok", tool_calls=None, prompt_tokens=10, completion_tokens=5
                ),
            ]

        store = MemoryContextStore()

        agent1 = Agent(MockProvider(responses=make_responses()), tools=tools, context_store=store)
        await agent1.run("run", session_id="sess_a")

        agent2 = Agent(MockProvider(responses=make_responses()), tools=tools, context_store=store)
        await agent2.run("run", session_id="sess_b")

        # sess_a sets counter=99, but sess_b starts fresh at 0
        assert values_seen == [0, 0]

    @pytest.mark.asyncio
    async def test_context_on_rule_match_result(self):
        """RunResult from rule match also has context."""
        from tantra import KeywordRule, RuleSet

        rules = RuleSet([KeywordRule(["hello"], "Hi there!", name="greeting")])
        agent = Agent(MockProvider(), rules=rules)
        result = await agent.run("hello")
        assert result.handled_by_rule
        assert result.context is not None
        assert isinstance(result.context, RunContext)

    def test_run_sync_with_session(self):
        """run_sync forwards session_id."""
        provider = MockProvider(responses=["OK"])
        agent = Agent(provider)
        result = agent.run_sync("Hi", session_id="sync_sess")
        assert result.output == "OK"
        assert result.context is not None
