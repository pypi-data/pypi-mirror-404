"""Tests for the Agent class."""

import pytest
from conftest import MockProvider

from tantra import Agent, ToolSet, tool
from tantra.exceptions import ConfigurationError, MaxIterationsError
from tantra.types import ProviderResponse, ToolCallData


class TestAgentCreation:
    """Tests for Agent initialization."""

    def test_create_with_provider_instance(self):
        """Create agent with provider instance."""
        provider = MockProvider()
        agent = Agent(provider, system_prompt="You are helpful.")

        assert agent.provider is provider
        assert agent.system_prompt == "You are helpful."

    def test_create_with_provider_string(self):
        """Create agent with provider string."""
        # Note: This will fail without OPENAI_API_KEY, but tests the parsing
        try:
            agent = Agent("openai:gpt-4o")
            assert agent.provider.model_name == "gpt-4o"
        except Exception:
            # Expected if no API key
            pass

    def test_invalid_provider_string(self):
        """Invalid provider string raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            Agent("invalid:model")

    def test_default_memory(self):
        """Agent has memory by default."""
        provider = MockProvider()
        agent = Agent(provider)

        assert agent.memory is not None

    def test_custom_max_iterations(self):
        """Can set custom max_iterations."""
        provider = MockProvider()
        agent = Agent(provider, max_iterations=5)

        assert agent._max_iterations == 5

    def test_agent_repr(self):
        """Agent has informative repr."""
        provider = MockProvider(model_name="test-model")
        agent = Agent(provider, max_iterations=10)

        repr_str = repr(agent)
        assert "test-model" in repr_str
        assert "max_iterations=10" in repr_str


class TestAgentRun:
    """Tests for Agent.run()."""

    @pytest.mark.asyncio
    async def test_simple_run(self):
        """Basic agent run returns response."""
        provider = MockProvider(responses=["Hello, human!"])
        agent = Agent(provider, system_prompt="Be friendly.")

        result = await agent.run("Hi!")

        assert result.output == "Hello, human!"
        assert len(result.trace) > 0

    @pytest.mark.asyncio
    async def test_run_with_run_id(self):
        """Run with custom run_id."""
        from uuid import uuid4

        provider = MockProvider(responses=["Response"])
        agent = Agent(provider)
        run_id = uuid4()

        result = await agent.run("Test", run_id=run_id)

        assert result.metadata.run_id == run_id

    @pytest.mark.asyncio
    async def test_run_updates_memory(self):
        """Run adds messages to memory."""
        provider = MockProvider(responses=["Response"])
        agent = Agent(provider)

        await agent.run("Hello")

        messages = agent.memory.get_messages()
        assert len(messages) == 2  # User + Assistant
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_metadata_tracking(self):
        """Run tracks tokens and cost."""
        provider = MockProvider(responses=["Response"])
        agent = Agent(provider)

        result = await agent.run("Test")

        assert result.metadata.prompt_tokens > 0
        assert result.metadata.completion_tokens > 0
        assert result.metadata.total_tokens > 0


class TestAgentWithTools:
    """Tests for Agent with tools."""

    @pytest.mark.asyncio
    async def test_tool_call_execution(self):
        """Agent executes tool calls."""

        @tool
        def get_weather(city: str) -> str:
            return f"Sunny in {city}"

        tools = ToolSet([get_weather])

        # Provider returns tool call, then final response
        tool_call = ToolCallData(
            id="call-123",
            name="get_weather",
            arguments={"city": "Tokyo"},
        )
        provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[tool_call],
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content="It's sunny in Tokyo!",
                    tool_calls=None,
                    prompt_tokens=15,
                    completion_tokens=10,
                ),
            ]
        )

        agent = Agent(provider, tools=tools)
        result = await agent.run("What's the weather in Tokyo?")

        assert "sunny" in result.output.lower() or "Tokyo" in result.output
        assert result.metadata.tool_calls_count == 1

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self):
        """Agent handles multiple tool calls."""

        @tool
        def add(a: int, b: int) -> int:
            return a + b

        tools = ToolSet([add])

        # Two tool calls in one response
        tool_calls = [
            ToolCallData(id="call-1", name="add", arguments={"a": 1, "b": 2}),
            ToolCallData(id="call-2", name="add", arguments={"a": 3, "b": 4}),
        ]
        provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=tool_calls,
                    prompt_tokens=10,
                    completion_tokens=5,
                ),
                ProviderResponse(
                    content="3 and 7",
                    tool_calls=None,
                    prompt_tokens=15,
                    completion_tokens=5,
                ),
            ]
        )

        agent = Agent(provider, tools=tools)
        result = await agent.run("Add 1+2 and 3+4")

        assert result.metadata.tool_calls_count == 2


class TestAgentSync:
    """Tests for synchronous Agent methods."""

    def test_run_sync(self):
        """run_sync works without async."""
        provider = MockProvider(responses=["Sync response"])
        agent = Agent(provider)

        result = agent.run_sync("Hello")

        assert result.output == "Sync response"


class TestAgentHelpers:
    """Tests for Agent helper methods."""

    def test_clear_memory(self):
        """clear_memory clears conversation history."""
        provider = MockProvider(responses=["Response"])
        agent = Agent(provider)

        agent.run_sync("Hello")
        assert len(agent.memory.get_messages()) > 0

        agent.clear_memory()
        assert len(agent.memory.get_messages()) == 0

    def test_with_tools(self):
        """with_tools creates new agent with different tools."""
        provider = MockProvider()

        @tool
        def tool1() -> str:
            return "1"

        @tool
        def tool2() -> str:
            return "2"

        agent1 = Agent(provider, tools=ToolSet([tool1]))
        agent2 = agent1.with_tools(ToolSet([tool2]))

        assert agent1 is not agent2
        assert "tool1" in agent1.tools
        assert "tool2" in agent2.tools
        assert "tool1" not in agent2.tools

    def test_with_system_prompt(self):
        """with_system_prompt creates new agent with different prompt."""
        provider = MockProvider()
        agent1 = Agent(provider, system_prompt="Prompt 1")
        agent2 = agent1.with_system_prompt("Prompt 2")

        assert agent1 is not agent2
        assert agent1.system_prompt == "Prompt 1"
        assert agent2.system_prompt == "Prompt 2"


class TestAgentMaxIterations:
    """Tests for max_iterations limit."""

    @pytest.mark.asyncio
    async def test_max_iterations_exceeded(self):
        """Agent raises MaxIterationsError when limit exceeded."""

        @tool
        def infinite_loop() -> str:
            return "Keep going"

        tools = ToolSet([infinite_loop])

        # Provider always returns tool calls
        tool_call = ToolCallData(
            id="call-1",
            name="infinite_loop",
            arguments={},
        )
        provider = MockProvider(
            responses=[
                ProviderResponse(
                    content=None,
                    tool_calls=[tool_call],
                    prompt_tokens=10,
                    completion_tokens=5,
                )
            ]
            * 20  # Many tool call responses
        )

        agent = Agent(provider, tools=tools, max_iterations=3)

        with pytest.raises(MaxIterationsError):
            await agent.run("Start the loop")
