"""Observability components for Tantra.

Provides logging, cost tracking, and OpenTelemetry instrumentation.

Example:
    from tantra.observability import Logger, CostTracker
    from tantra.observability import instrument, span

    # Simple logging
    logger = Logger()
    logger.log_prompt(messages)
    logger.log_llm_response(content, tool_calls, prompt_tokens, completion_tokens)

    # OpenTelemetry instrumentation
    instrument(service_name="my-agent")

    with span("custom_operation") as s:
        # ... do work ...
        s.set_attribute("result", "success")
"""

# Re-export LogEntry from types for backwards compatibility
from ..types import LogEntry

# Logging and cost tracking
from .logging import (
    CostTracker,
    Logger,
    console_logger,
    create_run_metadata,
)

# OpenTelemetry instrumentation
from .telemetry import (
    SpanAttributes,
    get_meter,
    get_tracer,
    # Setup
    instrument,
    is_instrumented,
    # Metrics recording
    record_agent_run,
    record_error,
    record_graph_node,
    record_llm_call,
    record_orchestration_run,
    record_rate_limit,
    record_rule_evaluation,
    record_swarm_handoff,
    record_tool_call,
    # Tracing
    span,
    trace_agent_run,
    trace_graph_run,
    trace_llm_call,
    trace_llm_stream,
    trace_orchestration_run,
    trace_react_run,
    trace_swarm_run,
    trace_tool_call,
    uninstrument,
)

__all__ = [
    # Types (re-exported)
    "LogEntry",
    # Logging
    "CostTracker",
    "Logger",
    "console_logger",
    "create_run_metadata",
    # Setup
    "instrument",
    "uninstrument",
    "is_instrumented",
    "get_tracer",
    "get_meter",
    # Tracing
    "span",
    "SpanAttributes",
    "trace_agent_run",
    "trace_llm_call",
    "trace_llm_stream",
    "trace_tool_call",
    "trace_orchestration_run",
    "trace_swarm_run",
    "trace_graph_run",
    "trace_react_run",
    # Metrics recording
    "record_agent_run",
    "record_llm_call",
    "record_tool_call",
    "record_rate_limit",
    "record_orchestration_run",
    "record_swarm_handoff",
    "record_graph_node",
    "record_rule_evaluation",
    "record_error",
]
