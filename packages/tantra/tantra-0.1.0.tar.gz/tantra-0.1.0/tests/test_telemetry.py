"""Tests for OpenTelemetry instrumentation."""

import pytest

from tantra.observability.telemetry import (
    SpanAttributes,
    _NoOpSpan,
    instrument,
    is_instrumented,
    span,
    uninstrument,
)


class TestInstrument:
    """Tests for instrument/uninstrument."""

    def setup_method(self):
        """Reset instrumentation before each test."""
        uninstrument()

    def teardown_method(self):
        """Clean up after each test."""
        uninstrument()

    def test_instrument_basic(self):
        """Basic instrumentation works."""
        assert not is_instrumented()
        instrument()
        assert is_instrumented()

    def test_instrument_idempotent(self):
        """Multiple calls to instrument() are no-ops."""
        instrument()
        instrument()
        instrument()
        assert is_instrumented()

    def test_uninstrument(self):
        """uninstrument() disables tracing."""
        instrument()
        assert is_instrumented()
        uninstrument()
        assert not is_instrumented()

    def test_instrument_with_service_name(self):
        """Custom service name is accepted."""
        instrument(service_name="my-test-service")
        assert is_instrumented()

    def test_instrument_with_console(self):
        """Console exporter can be enabled."""
        instrument(console=True)
        assert is_instrumented()


class TestSpan:
    """Tests for span context manager."""

    def setup_method(self):
        uninstrument()

    def teardown_method(self):
        uninstrument()

    def test_span_without_instrumentation(self):
        """span() works even when not instrumented (no-op)."""
        assert not is_instrumented()

        with span("test.span", {"key": "value"}) as s:
            assert isinstance(s, _NoOpSpan)
            # Should not raise
            s.set_attribute("foo", "bar")
            s.add_event("event")

    def test_span_with_instrumentation(self):
        """span() creates real spans when instrumented."""
        instrument(console=False)

        with span("test.span", {"test_attr": "value"}) as s:
            # Should be a real span, not NoOpSpan
            assert not isinstance(s, _NoOpSpan)
            s.set_attribute("another", "attr")


class TestNoOpSpan:
    """Tests for _NoOpSpan."""

    def test_noop_methods(self):
        """All methods work without errors."""
        s = _NoOpSpan()

        # None of these should raise
        s.set_attribute("key", "value")
        s.set_attributes({"a": 1, "b": 2})
        s.add_event("event_name", {"attr": "value"})
        s.record_exception(ValueError("test"))
        s.set_status(None)


class TestSpanAttributes:
    """Tests for SpanAttributes constants."""

    def test_agent_attributes_exist(self):
        """Agent attributes are defined."""
        assert SpanAttributes.name == "tantra.agent.name"
        assert SpanAttributes.AGENT_MODEL == "tantra.agent.model"

    def test_llm_attributes_follow_conventions(self):
        """LLM attributes follow gen_ai semantic conventions."""
        assert SpanAttributes.LLM_MODEL == "gen_ai.request.model"
        assert SpanAttributes.LLM_PROMPT_TOKENS == "gen_ai.usage.prompt_tokens"

    def test_tool_attributes_exist(self):
        """Tool attributes are defined."""
        assert SpanAttributes.TOOL_NAME == "tantra.tool.name"
        assert SpanAttributes.TOOL_SUCCESS == "tantra.tool.success"


class TestEnvironmentVariables:
    """Tests for environment variable configuration."""

    def setup_method(self):
        uninstrument()

    def teardown_method(self):
        uninstrument()

    def test_service_name_from_env(self):
        """Service name can come from environment."""
        import os

        old_val = os.environ.get("OTEL_SERVICE_NAME")

        try:
            os.environ["OTEL_SERVICE_NAME"] = "test-from-env"
            instrument()
            assert is_instrumented()
        finally:
            if old_val:
                os.environ["OTEL_SERVICE_NAME"] = old_val
            else:
                os.environ.pop("OTEL_SERVICE_NAME", None)


class TestTraceToolCall:
    """Tests for trace_tool_call function."""

    def setup_method(self):
        uninstrument()

    def teardown_method(self):
        uninstrument()

    def test_trace_tool_call_without_instrumentation(self):
        """trace_tool_call is no-op without instrumentation."""
        from tantra.observability.telemetry import trace_tool_call

        # Should not raise
        trace_tool_call(
            tool_name="test_tool",
            arguments={"arg": "value"},
            result="test result",
            success=True,
            duration_ms=100,
        )

    def test_trace_tool_call_with_instrumentation(self):
        """trace_tool_call records event when instrumented."""
        from tantra.observability.telemetry import trace_tool_call

        instrument()

        with span("parent.span"):
            trace_tool_call(
                tool_name="get_weather",
                arguments={"city": "Tokyo"},
                result="Sunny, 25C",
                success=True,
                duration_ms=150,
            )
        # Should complete without errors


class TestIntegration:
    """Integration tests with Agent."""

    def setup_method(self):
        uninstrument()

    def teardown_method(self):
        uninstrument()

    @pytest.mark.asyncio
    async def test_agent_run_with_telemetry(self):
        """Agent runs work with telemetry enabled."""
        import sys

        from tantra import Agent

        sys.path.insert(0, "tests")
        from conftest import MockProvider

        instrument(console=False)

        agent = Agent(
            MockProvider(responses=["Hello!"]),
            name="test-agent",
        )

        result = await agent.run("Hi")

        assert result.output == "Hello!"
        assert is_instrumented()

    @pytest.mark.asyncio
    async def test_agent_run_without_telemetry(self):
        """Agent runs work without telemetry."""
        import sys

        from tantra import Agent

        sys.path.insert(0, "tests")
        from conftest import MockProvider

        assert not is_instrumented()

        agent = Agent(MockProvider(responses=["Hello!"]))
        result = await agent.run("Hi")

        assert result.output == "Hello!"
