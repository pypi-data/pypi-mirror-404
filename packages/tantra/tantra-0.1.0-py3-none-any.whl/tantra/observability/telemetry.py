"""OpenTelemetry instrumentation for Tantra.

Provides automatic tracing and metrics for agent runs, LLM calls, and tool executions.
Follows standard OpenTelemetry patterns and conventions.

Setup (choose one):

    # Option 1: Environment variables (recommended)
    # Set OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME, etc.
    from tantra.observability import instrument
    instrument()

    # Option 2: Explicit configuration
    from tantra.observability import instrument
    instrument(
        service_name="my-agent-service",
        endpoint="http://localhost:4317",
    )

    # Option 3: Use existing tracer provider
    # If you already have OTEL configured, just call instrument()
    from tantra.observability import instrument
    instrument()  # Uses global tracer provider

Environment Variables (standard OTEL):
    OTEL_SERVICE_NAME: Service name (default: "tantra")
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (e.g., http://localhost:4317)
    OTEL_EXPORTER_OTLP_HEADERS: Headers for auth (e.g., "api-key=xxx")
    OTEL_TRACES_EXPORTER: Exporter type (otlp, console, none)
    OTEL_METRICS_EXPORTER: Metrics exporter type (otlp, console, none)
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

# Lazy imports - only load OTEL when actually used
_tracer = None
_meter = None
_instrumented = False

# Metrics instruments (initialized on instrument())
_metrics: dict[str, Any] = {}


def instrument(
    service_name: str | None = None,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
    console: bool = False,
) -> None:
    """Instrument Tantra with OpenTelemetry tracing and metrics.

    Call this once at application startup. Subsequent calls are no-ops.

    Args:
        service_name: Service name for traces/metrics. Defaults to OTEL_SERVICE_NAME
            env var or "tantra".
        endpoint: OTLP exporter endpoint. Defaults to OTEL_EXPORTER_OTLP_ENDPOINT.
            If not set and console=False, uses existing providers.
        headers: Headers for OTLP exporter (e.g., for authentication).
            Defaults to OTEL_EXPORTER_OTLP_HEADERS.
        console: If True, also print spans/metrics to console (useful for debugging).

    Examples:
        ```python
        # Using environment variables
        import os
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://jaeger:4317"
        instrument()

        # Or explicit configuration
        instrument(
            service_name="my-agent",
            endpoint="http://jaeger:4317",
        )
        ```
    """
    global _tracer, _meter, _instrumented, _metrics

    if _instrumented:
        return

    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    # Resolve configuration from args or environment
    service = service_name or os.environ.get("OTEL_SERVICE_NAME", "tantra")
    otlp_endpoint = endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    trace_exporter_type = os.environ.get("OTEL_TRACES_EXPORTER", "otlp")
    metrics_exporter_type = os.environ.get("OTEL_METRICS_EXPORTER", "otlp")

    # Create shared resource
    resource = Resource.create({SERVICE_NAME: service})

    # Parse headers
    otlp_headers = headers
    if not otlp_headers:
        headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
        if headers_str:
            otlp_headers = dict(
                item.split("=", 1) for item in headers_str.split(",") if "=" in item
            )

    # =========================================================================
    # Setup Tracing
    # =========================================================================
    current_trace_provider = trace.get_tracer_provider()
    is_default_trace_provider = type(current_trace_provider).__name__ == "ProxyTracerProvider"

    if is_default_trace_provider:
        trace_provider = TracerProvider(resource=resource)

        # Add OTLP exporter if endpoint is configured
        if otlp_endpoint and trace_exporter_type != "none":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                headers=otlp_headers,
            )
            trace_provider.add_span_processor(BatchSpanProcessor(exporter))

        # Add console exporter if requested
        if console or trace_exporter_type == "console":
            trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(trace_provider)

    # Get tracer for Tantra
    _tracer = trace.get_tracer("tantra", "0.1.0")

    # =========================================================================
    # Setup Metrics
    # =========================================================================
    metric_readers = []

    # Add OTLP metrics exporter if endpoint is configured
    if otlp_endpoint and metrics_exporter_type != "none":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

            metric_exporter = OTLPMetricExporter(
                endpoint=otlp_endpoint,
                headers=otlp_headers,
            )
            metric_readers.append(PeriodicExportingMetricReader(metric_exporter))
        except ImportError:
            pass  # OTLP metrics exporter not available

    # Add console exporter if requested
    if console or metrics_exporter_type == "console":
        metric_readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))

    # Create meter provider
    if metric_readers:
        meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
        metrics.set_meter_provider(meter_provider)

    # Get meter for Tantra
    _meter = metrics.get_meter("tantra", "0.1.0")

    # =========================================================================
    # Create Metrics Instruments
    # =========================================================================
    _metrics = _create_metrics(_meter)

    _instrumented = True


def _create_metrics(meter: Any) -> dict[str, Any]:
    """Create all OTEL metrics instruments.

    Args:
        meter: The OTEL Meter instance to create instruments on.

    Returns:
        Dict mapping metric names to their OTEL instrument objects.
    """
    m = {}

    # -------------------------------------------------------------------------
    # Agent Metrics
    # -------------------------------------------------------------------------
    m["agent_runs_total"] = meter.create_counter(
        name="tantra.agent.runs.total",
        description="Total number of agent runs",
        unit="1",
    )
    m["agent_runs_duration"] = meter.create_histogram(
        name="tantra.agent.runs.duration",
        description="Agent run duration in milliseconds",
        unit="ms",
    )
    m["agent_runs_iterations"] = meter.create_histogram(
        name="tantra.agent.runs.iterations",
        description="Number of LLM iterations per agent run",
        unit="1",
    )

    # -------------------------------------------------------------------------
    # LLM Metrics
    # -------------------------------------------------------------------------
    m["llm_calls_total"] = meter.create_counter(
        name="tantra.llm.calls.total",
        description="Total number of LLM calls",
        unit="1",
    )
    m["llm_calls_duration"] = meter.create_histogram(
        name="tantra.llm.calls.duration",
        description="LLM call duration in milliseconds",
        unit="ms",
    )
    m["llm_tokens_prompt"] = meter.create_counter(
        name="tantra.llm.tokens.prompt",
        description="Total prompt tokens consumed",
        unit="1",
    )
    m["llm_tokens_completion"] = meter.create_counter(
        name="tantra.llm.tokens.completion",
        description="Total completion tokens consumed",
        unit="1",
    )
    m["llm_cost_total"] = meter.create_counter(
        name="tantra.llm.cost.total",
        description="Total estimated cost in USD",
        unit="USD",
    )

    # -------------------------------------------------------------------------
    # Tool Metrics
    # -------------------------------------------------------------------------
    m["tool_calls_total"] = meter.create_counter(
        name="tantra.tool.calls.total",
        description="Total number of tool calls",
        unit="1",
    )
    m["tool_calls_duration"] = meter.create_histogram(
        name="tantra.tool.calls.duration",
        description="Tool execution duration in milliseconds",
        unit="ms",
    )
    m["tool_errors_total"] = meter.create_counter(
        name="tantra.tool.errors.total",
        description="Total number of tool errors",
        unit="1",
    )

    # -------------------------------------------------------------------------
    # Rate Limiting Metrics
    # -------------------------------------------------------------------------
    m["ratelimit_throttled_total"] = meter.create_counter(
        name="tantra.ratelimit.throttled.total",
        description="Total number of requests throttled by rate limiter",
        unit="1",
    )
    m["ratelimit_wait_duration"] = meter.create_histogram(
        name="tantra.ratelimit.wait.duration",
        description="Time spent waiting for rate limiter in milliseconds",
        unit="ms",
    )

    # -------------------------------------------------------------------------
    # Orchestration Metrics
    # -------------------------------------------------------------------------
    m["orchestration_runs_total"] = meter.create_counter(
        name="tantra.orchestration.runs.total",
        description="Total number of orchestration runs",
        unit="1",
    )
    m["orchestration_runs_duration"] = meter.create_histogram(
        name="tantra.orchestration.runs.duration",
        description="Orchestration run duration in milliseconds",
        unit="ms",
    )
    m["swarm_handoffs_total"] = meter.create_counter(
        name="tantra.swarm.handoffs.total",
        description="Total number of swarm handoffs",
        unit="1",
    )
    m["graph_nodes_executed"] = meter.create_counter(
        name="tantra.graph.nodes.executed",
        description="Total number of graph nodes executed",
        unit="1",
    )

    # -------------------------------------------------------------------------
    # Rule Metrics (Automation-First)
    # -------------------------------------------------------------------------
    m["rules_evaluations_total"] = meter.create_counter(
        name="tantra.rules.evaluations.total",
        description="Total number of rule evaluations",
        unit="1",
    )
    m["rules_matches_total"] = meter.create_counter(
        name="tantra.rules.matches.total",
        description="Total number of rule matches (requests handled without LLM)",
        unit="1",
    )

    # -------------------------------------------------------------------------
    # Error Metrics
    # -------------------------------------------------------------------------
    m["errors_total"] = meter.create_counter(
        name="tantra.errors.total",
        description="Total number of errors",
        unit="1",
    )

    return m


def uninstrument() -> None:
    """Remove Tantra instrumentation. Mainly useful for testing."""
    global _tracer, _meter, _instrumented, _metrics
    _tracer = None
    _meter = None
    _instrumented = False
    _metrics = {}


def is_instrumented() -> bool:
    """Check if Tantra is instrumented with OpenTelemetry.

    Returns:
        True if ``instrument()`` has been called successfully.
    """
    return _instrumented


def get_tracer() -> Any:
    """Get the Tantra tracer.

    Returns:
        The OTEL tracer, or None if not instrumented.
    """
    return _tracer


def get_meter() -> Any:
    """Get the Tantra meter.

    Returns:
        The OTEL meter, or None if not instrumented.
    """
    return _meter


# =============================================================================
# Metrics Recording Functions
# =============================================================================


def record_agent_run(
    duration_ms: float,
    iterations: int,
    status: str = "success",
    name: str | None = None,
    model: str | None = None,
) -> None:
    """Record an agent run metric.

    Args:
        duration_ms: Run duration in milliseconds.
        iterations: Number of LLM iterations.
        status: "success" or "failure".
        name: Optional agent name.
        model: Optional model name.
    """
    if not _instrumented or not _metrics:
        return

    labels = {"status": status}
    if name:
        labels["name"] = name
    if model:
        labels["model"] = model

    _metrics["agent_runs_total"].add(1, labels)
    _metrics["agent_runs_duration"].record(duration_ms, labels)
    _metrics["agent_runs_iterations"].record(iterations, labels)


def record_llm_call(
    duration_ms: float,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    model: str,
    status: str = "success",
) -> None:
    """Record an LLM call metric.

    Args:
        duration_ms: Call duration in milliseconds.
        prompt_tokens: Number of prompt tokens.
        completion_tokens: Number of completion tokens.
        cost: Estimated cost in USD.
        model: Model name.
        status: "success" or "failure".
    """
    if not _instrumented or not _metrics:
        return

    labels = {"model": model, "status": status}

    _metrics["llm_calls_total"].add(1, labels)
    _metrics["llm_calls_duration"].record(duration_ms, labels)
    _metrics["llm_tokens_prompt"].add(prompt_tokens, {"model": model})
    _metrics["llm_tokens_completion"].add(completion_tokens, {"model": model})
    _metrics["llm_cost_total"].add(cost, {"model": model})


def record_tool_call(
    tool_name: str,
    duration_ms: float,
    success: bool,
    error_type: str | None = None,
) -> None:
    """Record a tool call metric.

    Args:
        tool_name: Name of the tool.
        duration_ms: Execution duration in milliseconds.
        success: Whether the call succeeded.
        error_type: Type of error if failed (validation, timeout, etc.).
    """
    if not _instrumented or not _metrics:
        return

    status = "success" if success else "failure"
    labels = {"tool_name": tool_name, "status": status}

    _metrics["tool_calls_total"].add(1, labels)
    _metrics["tool_calls_duration"].record(duration_ms, labels)

    if not success:
        error_labels = {"tool_name": tool_name, "error_type": error_type or "unknown"}
        _metrics["tool_errors_total"].add(1, error_labels)


def record_rate_limit(
    wait_ms: float,
    throttled: bool,
    model: str | None = None,
) -> None:
    """Record a rate limiting event.

    Args:
        wait_ms: Time spent waiting in milliseconds.
        throttled: Whether the request was throttled.
        model: Optional model name.
    """
    if not _instrumented or not _metrics:
        return

    labels = {"model": model or "unknown"}

    if throttled:
        _metrics["ratelimit_throttled_total"].add(1, labels)

    if wait_ms > 0:
        _metrics["ratelimit_wait_duration"].record(wait_ms, labels)


def record_orchestration_run(
    orchestration_type: str,
    duration_ms: float,
    status: str = "success",
) -> None:
    """Record an orchestration run metric.

    Args:
        orchestration_type: Type (pipeline, router, parallel, supervisor, swarm).
        duration_ms: Run duration in milliseconds.
        status: "success" or "failure".
    """
    if not _instrumented or not _metrics:
        return

    labels = {"type": orchestration_type, "status": status}

    _metrics["orchestration_runs_total"].add(1, labels)
    _metrics["orchestration_runs_duration"].record(duration_ms, labels)


def record_swarm_handoff(
    from_agent: str,
    to_agent: str,
) -> None:
    """Record a swarm handoff.

    Args:
        from_agent: Source agent name.
        to_agent: Target agent name.
    """
    if not _instrumented or not _metrics:
        return

    labels = {"from_agent": from_agent, "to_agent": to_agent}
    _metrics["swarm_handoffs_total"].add(1, labels)


def record_graph_node(
    graph_name: str,
    node_id: str,
) -> None:
    """Record a graph node execution.

    Args:
        graph_name: Name of the graph.
        node_id: ID of the executed node.
    """
    if not _instrumented or not _metrics:
        return

    labels = {"graph_name": graph_name, "node_id": node_id}
    _metrics["graph_nodes_executed"].add(1, labels)


def record_rule_evaluation(
    matched: bool,
    rule_name: str | None = None,
) -> None:
    """Record a rule evaluation.

    Args:
        matched: Whether a rule matched.
        rule_name: Name of the matched rule (if any).
    """
    if not _instrumented or not _metrics:
        return

    _metrics["rules_evaluations_total"].add(1, {"matched": str(matched).lower()})

    if matched and rule_name:
        _metrics["rules_matches_total"].add(1, {"rule_name": rule_name})


def record_error(
    error_type: str,
    component: str,
) -> None:
    """Record an error.

    Args:
        error_type: Type of error (validation, timeout, rate_limit, api_error, tool_error).
        component: Component where error occurred (agent, llm, tool, orchestration).
    """
    if not _instrumented or not _metrics:
        return

    labels = {"error_type": error_type, "component": component}
    _metrics["errors_total"].add(1, labels)


# =============================================================================
# Trace Span Utilities
# =============================================================================


@contextmanager
def span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """Create a trace span.

    Use this to instrument custom operations:

        with span("my_operation", {"key": "value"}) as s:
            # ... do work ...
            s.set_attribute("result", "success")

    Args:
        name: Span name (e.g., "agent.run", "llm.call")
        attributes: Initial span attributes

    Yields:
        The span object (or a no-op if not instrumented)
    """
    if not _instrumented or _tracer is None:
        yield _NoOpSpan()
        return

    with _tracer.start_as_current_span(name, attributes=attributes) as s:
        yield s


class _NoOpSpan:
    """No-op span when telemetry is not enabled."""

    def set_attribute(self, key: str, value: Any) -> None:
        """No-op: ignore attribute."""

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        """No-op: ignore attributes."""

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """No-op: ignore event."""

    def record_exception(self, exception: Exception) -> None:
        """No-op: ignore exception."""

    def set_status(self, status: Any) -> None:
        """No-op: ignore status."""


# =============================================================================
# Semantic Conventions
# =============================================================================


class SpanAttributes:
    """Standard attribute names for Tantra spans.

    Following OpenTelemetry semantic conventions where applicable.
    """

    # Agent attributes
    name = "tantra.agent.name"
    AGENT_MODEL = "tantra.agent.model"
    AGENT_MAX_ITERATIONS = "tantra.agent.max_iterations"

    # Run attributes
    RUN_ID = "tantra.run.id"
    RUN_PARENT_ID = "tantra.run.parent_id"
    RUN_INPUT = "tantra.run.input"
    RUN_OUTPUT = "tantra.run.output"
    RUN_ITERATIONS = "tantra.run.iterations"

    # LLM attributes (following gen_ai semantic conventions)
    LLM_SYSTEM = "gen_ai.system"  # e.g., "openai"
    LLM_MODEL = "gen_ai.request.model"
    LLM_TEMPERATURE = "gen_ai.request.temperature"
    LLM_MAX_TOKENS = "gen_ai.request.max_tokens"
    LLM_PROMPT_TOKENS = "gen_ai.usage.prompt_tokens"
    LLM_COMPLETION_TOKENS = "gen_ai.usage.completion_tokens"
    LLM_TOTAL_TOKENS = "gen_ai.usage.total_tokens"
    LLM_DURATION_MS = "gen_ai.duration_ms"
    LLM_STREAMING = "gen_ai.streaming"

    # Tool attributes
    TOOL_NAME = "tantra.tool.name"
    TOOL_ARGUMENTS = "tantra.tool.arguments"
    TOOL_RESULT = "tantra.tool.result"
    TOOL_SUCCESS = "tantra.tool.success"
    TOOL_DURATION_MS = "tantra.tool.duration_ms"

    # Cost attributes
    COST_ESTIMATED = "tantra.cost.estimated_usd"

    # Orchestration attributes
    ORCHESTRATION_TYPE = "tantra.orchestration.type"
    ORCHESTRATION_AGENTS = "tantra.orchestration.agents"
    ORCHESTRATION_STEPS = "tantra.orchestration.steps"
    ORCHESTRATION_TOTAL_TOKENS = "tantra.orchestration.total_tokens"
    ORCHESTRATION_TOTAL_COST = "tantra.orchestration.total_cost"

    # Router attributes
    ROUTER_METHOD = "tantra.router.method"
    ROUTER_SELECTED_AGENT = "tantra.router.selected_agent"
    ROUTER_AVAILABLE_AGENTS = "tantra.router.available_agents"

    # Swarm attributes
    SWARM_ENTRY_POINT = "tantra.swarm.entry_point"
    SWARM_HANDOFF_COUNT = "tantra.swarm.handoff_count"
    SWARM_HANDOFF_CHAIN = "tantra.swarm.handoff_chain"
    SWARM_HANDOFF_FROM = "tantra.swarm.handoff.from"
    SWARM_HANDOFF_TO = "tantra.swarm.handoff.to"
    SWARM_HANDOFF_REASON = "tantra.swarm.handoff.reason"

    # Graph attributes
    GRAPH_NAME = "tantra.graph.name"
    GRAPH_NODES_EXECUTED = "tantra.graph.nodes_executed"
    GRAPH_EXECUTION_PATH = "tantra.graph.execution_path"
    GRAPH_NODE_ID = "tantra.graph.node.id"
    GRAPH_NODE_TYPE = "tantra.graph.node.type"

    # ReAct attributes
    REACT_ITERATIONS = "tantra.react.iterations"
    REACT_THOUGHT = "tantra.react.thought"
    REACT_ACTION = "tantra.react.action"


# =============================================================================
# Trace Decorators
# =============================================================================


def trace_agent_run(func: Callable) -> Callable:
    """Decorator to trace agent run methods.

    Automatically creates spans and records metrics.

    Args:
        func: The async agent run method to wrap.

    Returns:
        Wrapped function with tracing instrumentation.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, user_input: str, *args, **kwargs):
        start_time = time.time()

        if not _instrumented:
            return await func(self, user_input, *args, **kwargs)

        model_name = getattr(self._provider, "model_name", "unknown")
        name = getattr(self, "_name", None)

        attrs = {
            SpanAttributes.AGENT_MODEL: model_name,
            SpanAttributes.RUN_INPUT: user_input[:500],
        }

        if name:
            attrs[SpanAttributes.name] = name

        with span("agent.run", attrs) as s:
            try:
                result = await func(self, user_input, *args, **kwargs)

                # Add result attributes to span
                s.set_attribute(SpanAttributes.RUN_OUTPUT, result.output[:500])
                s.set_attribute(SpanAttributes.RUN_ITERATIONS, result.metadata.iterations)
                s.set_attribute(SpanAttributes.LLM_PROMPT_TOKENS, result.metadata.prompt_tokens)
                s.set_attribute(
                    SpanAttributes.LLM_COMPLETION_TOKENS, result.metadata.completion_tokens
                )
                s.set_attribute(SpanAttributes.LLM_TOTAL_TOKENS, result.metadata.total_tokens)
                s.set_attribute(SpanAttributes.COST_ESTIMATED, result.metadata.estimated_cost)

                # Record metrics
                duration_ms = (time.time() - start_time) * 1000
                record_agent_run(
                    duration_ms=duration_ms,
                    iterations=result.metadata.iterations,
                    status="success",
                    name=name,
                    model=model_name,
                )

                # Record rule evaluation
                if hasattr(result, "rule_match") and result.rule_match is not None:
                    record_rule_evaluation(matched=True, rule_name=result.rule_match.rule_name)
                else:
                    record_rule_evaluation(matched=False)

                return result

            except Exception as e:
                s.record_exception(e)

                # Record metrics
                duration_ms = (time.time() - start_time) * 1000
                record_agent_run(
                    duration_ms=duration_ms,
                    iterations=0,
                    status="failure",
                    name=name,
                    model=model_name,
                )
                record_error(error_type=type(e).__name__, component="agent")

                raise

    return wrapper


def trace_llm_call(func: Callable) -> Callable:
    """Decorator to trace LLM provider calls.

    Args:
        func: The async LLM call method to wrap.

    Returns:
        Wrapped function with tracing instrumentation.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, messages, *args, **kwargs):
        start_time = time.time()

        if not _instrumented:
            return await func(self, messages, *args, **kwargs)

        model_name = getattr(self, "model_name", "unknown")

        provider_name = getattr(self, "provider_name", "unknown")

        attrs = {
            SpanAttributes.LLM_SYSTEM: provider_name,
            SpanAttributes.LLM_MODEL: model_name,
        }

        with span("llm.call", attrs) as s:
            try:
                response = await func(self, messages, *args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Add span attributes
                s.set_attribute(SpanAttributes.LLM_PROMPT_TOKENS, response.prompt_tokens)
                s.set_attribute(SpanAttributes.LLM_COMPLETION_TOKENS, response.completion_tokens)
                s.set_attribute(SpanAttributes.LLM_DURATION_MS, duration_ms)

                # Calculate cost
                cost_per_1k_input = getattr(self, "cost_per_1k_input", 0.0)
                cost_per_1k_output = getattr(self, "cost_per_1k_output", 0.0)
                cost = (response.prompt_tokens * cost_per_1k_input / 1000) + (
                    response.completion_tokens * cost_per_1k_output / 1000
                )

                # Record metrics
                record_llm_call(
                    duration_ms=duration_ms,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    cost=cost,
                    model=model_name,
                    status="success",
                )

                return response

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                s.record_exception(e)

                # Determine error type
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    error_type = "rate_limit"
                    record_rate_limit(wait_ms=0, throttled=True, model=model_name)
                elif "timeout" in error_str:
                    error_type = "timeout"
                else:
                    error_type = "api_error"

                record_error(error_type=error_type, component="llm")

                raise

    return wrapper


def trace_tool_call_decorator(func: Callable) -> Callable:
    """Decorator to trace tool executions.

    Args:
        func: The async tool execution method to wrap.

    Returns:
        Wrapped function with tracing instrumentation.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        tool_name = getattr(self, "name", "unknown")

        try:
            result = await func(self, *args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000
            record_tool_call(
                tool_name=tool_name,
                duration_ms=duration_ms,
                success=True,
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Determine error type
            error_type = "tool_error"
            if "validation" in type(e).__name__.lower():
                error_type = "validation"
            elif "timeout" in str(e).lower():
                error_type = "timeout"

            record_tool_call(
                tool_name=tool_name,
                duration_ms=duration_ms,
                success=False,
                error_type=error_type,
            )
            record_error(error_type=error_type, component="tool")

            raise

    return wrapper


def trace_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    result: Any = None,
    success: bool = True,
    duration_ms: float = 0,
) -> None:
    """Record a tool call as a span event.

    Call this after executing a tool to record it in the current span.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments
        result: Tool result (will be truncated)
        success: Whether the tool succeeded
        duration_ms: Execution duration in milliseconds
    """
    if not _instrumented or _tracer is None:
        return

    from opentelemetry import trace

    current_span = trace.get_current_span()
    if current_span:
        current_span.add_event(
            "tool.call",
            attributes={
                SpanAttributes.TOOL_NAME: tool_name,
                SpanAttributes.TOOL_ARGUMENTS: str(arguments)[:500],
                SpanAttributes.TOOL_RESULT: str(result)[:500] if result else "",
                SpanAttributes.TOOL_SUCCESS: success,
                SpanAttributes.TOOL_DURATION_MS: duration_ms,
            },
        )

    # Also record metric
    record_tool_call(
        tool_name=tool_name,
        duration_ms=duration_ms,
        success=success,
        error_type=None if success else "unknown",
    )


def trace_llm_stream(func: Callable) -> Callable:
    """Decorator to trace streaming LLM calls.

    Args:
        func: The async generator method to wrap.

    Returns:
        Wrapped async generator with tracing instrumentation.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, messages, *args, **kwargs):
        if not _instrumented:
            async for chunk in func(self, messages, *args, **kwargs):
                yield chunk
            return

        model_name = getattr(self, "model_name", "unknown")
        start_time = time.time()

        provider_name = getattr(self, "provider_name", "unknown")

        attrs = {
            SpanAttributes.LLM_SYSTEM: provider_name,
            SpanAttributes.LLM_MODEL: model_name,
            SpanAttributes.LLM_STREAMING: True,
        }

        with span("llm.stream", attrs) as s:
            try:
                token_count = 0
                async for chunk in func(self, messages, *args, **kwargs):
                    token_count += 1
                    yield chunk

                duration_ms = (time.time() - start_time) * 1000
                s.set_attribute("tantra.llm.chunks", token_count)
                s.set_attribute(SpanAttributes.LLM_DURATION_MS, duration_ms)

                # Record metrics (approximate - streaming doesn't give exact token counts)
                record_llm_call(
                    duration_ms=duration_ms,
                    prompt_tokens=0,  # Not available in streaming
                    completion_tokens=token_count,  # Approximate
                    cost=0.0,  # Can't calculate without token counts
                    model=model_name,
                    status="success",
                )

            except Exception as e:
                s.record_exception(e)
                record_error(error_type="streaming_error", component="llm")
                raise

    return wrapper


def trace_orchestration_run(orchestration_type: str) -> Callable:
    """Decorator factory to trace orchestration runs.

    Args:
        orchestration_type: Type of orchestration (pipeline, router, parallel, supervisor).

    Returns:
        A decorator that wraps async orchestration run methods with tracing.
    """

    def decorator(func: Callable) -> Callable:
        import functools
        import time

        @functools.wraps(func)
        async def wrapper(self, user_input: str, *args, **kwargs):
            start_time = time.time()

            if not _instrumented:
                return await func(self, user_input, *args, **kwargs)

            names = []
            if hasattr(self, "_agents"):
                if isinstance(self._agents, dict):
                    names = list(self._agents.keys())
                elif isinstance(self._agents, list):
                    names = [name for name, _ in self._agents]

            attrs = {
                SpanAttributes.ORCHESTRATION_TYPE: orchestration_type,
                SpanAttributes.RUN_INPUT: user_input[:500],
                SpanAttributes.ORCHESTRATION_AGENTS: ",".join(names),
            }

            with span(f"orchestration.{orchestration_type}", attrs) as s:
                try:
                    result = await func(self, user_input, *args, **kwargs)

                    duration_ms = (time.time() - start_time) * 1000

                    # Span attributes
                    s.set_attribute(SpanAttributes.RUN_OUTPUT, result.output[:500])
                    detail = result.detail
                    s.set_attribute(SpanAttributes.ORCHESTRATION_STEPS, len(detail.steps) if detail else 0)
                    s.set_attribute(SpanAttributes.ORCHESTRATION_TOTAL_TOKENS, result.metadata.total_tokens)
                    s.set_attribute(SpanAttributes.ORCHESTRATION_TOTAL_COST, result.metadata.estimated_cost)

                    # Add step events
                    for step in (detail.steps if detail else []):
                        s.add_event(
                            "orchestration.step",
                            attributes={
                                SpanAttributes.name: step.agent_id,
                                SpanAttributes.RUN_INPUT: step.input[:200],
                                SpanAttributes.RUN_OUTPUT: step.output[:200],
                                SpanAttributes.TOOL_DURATION_MS: step.duration_ms,
                            },
                        )

                    # Record metrics
                    record_orchestration_run(
                        orchestration_type=orchestration_type,
                        duration_ms=duration_ms,
                        status="success",
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    s.record_exception(e)

                    record_orchestration_run(
                        orchestration_type=orchestration_type,
                        duration_ms=duration_ms,
                        status="failure",
                    )
                    record_error(error_type=type(e).__name__, component="orchestration")

                    raise

        return wrapper

    return decorator


def trace_swarm_run(func: Callable) -> Callable:
    """Decorator to trace swarm runs with handoff tracking.

    Args:
        func: The async swarm run method to wrap.

    Returns:
        Wrapped function with tracing and handoff metrics.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, user_input: str, *args, **kwargs):
        start_time = time.time()

        if not _instrumented:
            return await func(self, user_input, *args, **kwargs)

        attrs = {
            SpanAttributes.ORCHESTRATION_TYPE: "swarm",
            SpanAttributes.RUN_INPUT: user_input[:500],
            SpanAttributes.SWARM_ENTRY_POINT: getattr(self, "_entry_point", "unknown"),
        }

        with span("swarm.run", attrs) as s:
            try:
                result = await func(self, user_input, *args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Span attributes
                s.set_attribute(SpanAttributes.RUN_OUTPUT, result.output[:500])
                detail = result.detail
                s.set_attribute(SpanAttributes.SWARM_HANDOFF_COUNT, detail.handoff_count if detail else 0)
                s.set_attribute(SpanAttributes.SWARM_HANDOFF_CHAIN, ",".join(detail.handoff_chain) if detail else "")
                s.set_attribute(SpanAttributes.ORCHESTRATION_TOTAL_TOKENS, result.metadata.total_tokens)
                s.set_attribute(SpanAttributes.ORCHESTRATION_TOTAL_COST, result.metadata.estimated_cost)

                # Add handoff events and record metrics
                for step in (detail.steps if detail else []):
                    if step.handoff_to:
                        s.add_event(
                            "swarm.handoff",
                            attributes={
                                SpanAttributes.SWARM_HANDOFF_FROM: step.agent_id,
                                SpanAttributes.SWARM_HANDOFF_TO: step.handoff_to,
                                SpanAttributes.SWARM_HANDOFF_REASON: step.handoff_reason or "",
                            },
                        )
                        record_swarm_handoff(from_agent=step.agent_id, to_agent=step.handoff_to)

                # Record orchestration metric
                record_orchestration_run(
                    orchestration_type="swarm",
                    duration_ms=duration_ms,
                    status="success",
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                s.record_exception(e)

                record_orchestration_run(
                    orchestration_type="swarm",
                    duration_ms=duration_ms,
                    status="failure",
                )
                record_error(error_type=type(e).__name__, component="swarm")

                raise

    return wrapper


def trace_graph_run(func: Callable) -> Callable:
    """Decorator to trace graph execution.

    Args:
        func: The async graph run method to wrap.

    Returns:
        Wrapped function with tracing and node metrics.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, input_text: str, *args, **kwargs):
        start_time = time.time()

        if not _instrumented:
            return await func(self, input_text, *args, **kwargs)

        graph_name = getattr(self, "name", "graph")

        attrs = {
            SpanAttributes.GRAPH_NAME: graph_name,
            SpanAttributes.RUN_INPUT: input_text[:500],
        }

        with span("graph.run", attrs) as s:
            try:
                result = await func(self, input_text, *args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Span attributes
                s.set_attribute(SpanAttributes.RUN_OUTPUT, result.output[:500])
                detail = result.detail
                s.set_attribute(
                    SpanAttributes.GRAPH_NODES_EXECUTED, ",".join(detail.nodes_executed) if detail else ""
                )
                s.set_attribute(
                    SpanAttributes.GRAPH_EXECUTION_PATH, ",".join(detail.execution_path) if detail else ""
                )
                s.set_attribute(SpanAttributes.RUN_ITERATIONS, detail.total_iterations if detail else 0)

                # Add node execution events and record metrics
                for node_id in (detail.nodes_executed if detail else []):
                    output = detail.state.node_outputs.get(node_id, "") if detail else ""
                    s.add_event(
                        "graph.node",
                        attributes={
                            SpanAttributes.GRAPH_NODE_ID: node_id,
                            SpanAttributes.RUN_OUTPUT: str(output)[:200],
                        },
                    )
                    record_graph_node(graph_name=graph_name, node_id=node_id)

                # Record orchestration metric
                record_orchestration_run(
                    orchestration_type="graph",
                    duration_ms=duration_ms,
                    status="success",
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                s.record_exception(e)

                record_orchestration_run(
                    orchestration_type="graph",
                    duration_ms=duration_ms,
                    status="failure",
                )
                record_error(error_type=type(e).__name__, component="graph")

                raise

    return wrapper


def trace_react_run(func: Callable) -> Callable:
    """Decorator to trace ReAct agent execution.

    Args:
        func: The async ReAct run method to wrap.

    Returns:
        Wrapped function with tracing and step metrics.
    """
    import functools
    import time

    @functools.wraps(func)
    async def wrapper(self, input_text: str, *args, **kwargs):
        start_time = time.time()

        if not _instrumented:
            return await func(self, input_text, *args, **kwargs)

        attrs = {
            SpanAttributes.RUN_INPUT: input_text[:500],
            SpanAttributes.AGENT_MAX_ITERATIONS: getattr(self, "max_iterations", 10),
        }

        with span("react.run", attrs) as s:
            try:
                result = await func(self, input_text, *args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Span attributes
                s.set_attribute(SpanAttributes.RUN_OUTPUT, result.output[:500])
                s.set_attribute(SpanAttributes.REACT_ITERATIONS, result.iterations)
                s.set_attribute(SpanAttributes.TOOL_SUCCESS, result.success)

                # Add step events
                for step in result.steps:
                    s.add_event(
                        "react.step",
                        attributes={
                            SpanAttributes.REACT_THOUGHT: (step.thought or "")[:200],
                            SpanAttributes.REACT_ACTION: step.action or "",
                            SpanAttributes.RUN_ITERATIONS: step.iteration,
                        },
                    )

                # Record orchestration metric
                record_orchestration_run(
                    orchestration_type="react",
                    duration_ms=duration_ms,
                    status="success" if result.success else "failure",
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                s.record_exception(e)

                record_orchestration_run(
                    orchestration_type="react",
                    duration_ms=duration_ms,
                    status="failure",
                )
                record_error(error_type=type(e).__name__, component="react")

                raise

    return wrapper
