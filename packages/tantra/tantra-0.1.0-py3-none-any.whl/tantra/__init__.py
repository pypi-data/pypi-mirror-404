# Tantra - A minimal, observable, production-ready AI agent framework
"""
Tantra is an AI agent framework designed for developers who build for production.
It combines simplicity with powerful features including first-class observability,
integrated evaluation, and extensible provider support.

Quick Start:
    from tantra import Agent, tool, ToolSet

    # Simple agent
    agent = Agent("openai:gpt-4o", system_prompt="You are helpful.")
    result = await agent.run("Hello!")
    print(result.output)

    # Agent with tools
    @tool
    def get_weather(city: str) -> str:
        return f"Weather in {city}: Sunny"

    agent = Agent("openai:gpt-4o", tools=ToolSet([get_weather]))
    result = await agent.run("What's the weather in Tokyo?")

In-the-Loop (ITL):
    from tantra import Agent, tool, ToolSet, CallbackInterruptHandler

    # Tool that requires human approval
    @tool(interrupt="Approve this refund?")
    def process_refund(amount: float) -> str:
        return f"Refunded ${amount}"

    async def notify(interrupt):
        print(f"Interrupt: {interrupt.prompt}")

    agent = Agent(
        "openai:gpt-4o",
        tools=ToolSet([process_refund]),
        interrupt_handler=CallbackInterruptHandler(notify),
    )
    # agent.run() raises ExecutionInterruptedError with checkpoint_id
    # Resume with: await agent.resume(checkpoint_id, InterruptResponse(...))
"""

__version__ = "0.1.0"

# Core classes
from tantra.agent import Agent

# Checkpoints
from tantra.checkpoints import (
    Checkpoint,
    CheckpointStore,
    PostgresCheckpointStore,
)
from tantra.context import ContextStore, MemoryContextStore, RunContext

# Types
from tantra.engine import AbortedError, ExecutionInterruptedError

# Evaluation
# Deployment
from tantra.evaluation import (
    BaselineStore,
    DegradationThresholds,
    DeploymentGate,
    DeploymentResult,
    DeploymentStatus,
    EvalCase,
    EvalResult,
    EvalSuite,
    FileBaselineStore,
    Matcher,
    MatchResult,
    PerformanceBaseline,
    PerformanceMonitor,
    # Matcher factory functions
    contains,
    cost_under,
    custom,
    deploy_with_gate,
    json_schema,
    json_valid,
    matches_regex,
    not_contains,
    tokens_under,
    tool_called,
    tool_not_called,
)

# Exceptions
from tantra.exceptions import (
    ConfigurationError,
    ContextMergeConflictError,
    MaxIterationsError,
    MCPConnectionError,
    MCPError,
    MCPToolExecutionError,
    ProviderError,
    TantraError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
)
from tantra.hooks import RunHooks

# In-the-Loop (ITL) and Warden Pattern
from tantra.intheloop import (
    # Registry
    AgentRegistry,
    CallbackInterruptHandler,
    # Interrupts
    Interrupt,
    InterruptHandler,
    InterruptResponse,
    # Warden Pattern
    Warden,
    WardenPreview,
    WardenTool,
    WardenToolSet,
    default_registry,
    get_agent,
    register_agent,
    warden_tool,
)
from tantra.mcp import MCPTools
from tantra.memory import ConversationMemory, Memory, WindowedMemory

# Observability
# OpenTelemetry Instrumentation (Traces + Metrics)
# Note: Requires opentelemetry packages for full functionality
# Install with: pip install tantra[telemetry]
from tantra.observability import (
    CostTracker,
    LogEntry,
    Logger,
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
    trace_swarm_run,
    trace_tool_call,
    uninstrument,
)

# Multi-Agent Orchestration (includes Pipeline, Router, Parallel, Graph, Swarm)
from tantra.orchestration import (
    AgentNode,
    AgentStep,
    Edge,
    EdgeCondition,
    FunctionNode,
    # Graph
    Graph,
    GraphBuilder,
    GraphDetail,
    GraphState,
    Handoff,
    Node,
    NodeType,
    OrchestrationDetail,
    # Base types
    Orchestrator,
    # Parallel
    Parallel,
    # Pipeline
    Pipeline,
    # Router
    Router,
    RouterNode,
    # Solo
    Solo,
    # Swarm
    Swarm,
    SwarmDetail,
    SwarmStep,
    chain,
    create_graph,
    fan_out,
    select,
    swarm,
)

# Providers
from tantra.providers.anthropic import AnthropicProvider

# Providers
from tantra.providers.base import ModelProvider
from tantra.providers.ollama import OllamaProvider
from tantra.providers.openai import OpenAIProvider

# Retry/Recovery
from tantra.resilience import (
    ANTHROPIC_TIER1,
    ANTHROPIC_TIER2,
    OPENAI_TIER1,
    OPENAI_TIER2,
    OPENAI_TIER3,
    BackoffStrategy,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    LoggingRetryCallback,
    RateLimitConfig,
    RateLimiter,
    RateLimitError,
    RetryableError,
    RetryCallback,
    RetryPolicy,
    RetryResult,
    retry_async,
    retry_sync,
    with_retry,
)
from tantra.retriever import Document, InMemoryRetriever, Retriever

# Automation-First Rules
from tantra.rules import (
    ConditionalRule,
    FunctionRule,
    KeywordRule,
    LookupRule,
    RegexRule,
    RejectRule,
    Rule,
    RuleMatch,
    RuleSet,
)

# Serve (HTTP API)
from tantra.serve import PostgresRunnableFactory, RunnableFactory, RunnableServer, serve
from tantra.tools import ToolDefinition, ToolSet, tool
from tantra.types import (
    ContentBlock,
    FileContent,
    ImageContent,
    LogType,
    Message,
    ProviderResponse,
    RunMetadata,
    RunResult,
    StreamChunk,
    StreamEvent,
    TextContent,
    ToolCallData,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "Agent",
    "tool",
    "ToolSet",
    "ToolDefinition",
    "MCPTools",
    # Context
    "RunContext",
    "ContextStore",
    "MemoryContextStore",
    # Lifecycle Hooks
    "RunHooks",
    # Rate Limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitError",
    "OPENAI_TIER1",
    "OPENAI_TIER2",
    "OPENAI_TIER3",
    "ANTHROPIC_TIER1",
    "ANTHROPIC_TIER2",
    # Memory
    "Memory",
    "ConversationMemory",
    "WindowedMemory",
    # Retriever (RAG)
    "Retriever",
    "Document",
    "InMemoryRetriever",
    # Observability
    "LogEntry",
    "Logger",
    "CostTracker",
    # Evaluation
    "EvalCase",
    "EvalSuite",
    "EvalResult",
    "Matcher",
    "MatchResult",
    "contains",
    "not_contains",
    "matches_regex",
    "json_valid",
    "json_schema",
    "tool_called",
    "tool_not_called",
    "cost_under",
    "tokens_under",
    "custom",
    # Providers
    "ModelProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    # Types
    "RunResult",
    "RunMetadata",
    "Message",
    "TextContent",
    "ImageContent",
    "FileContent",
    "ContentBlock",
    "LogType",
    "ProviderResponse",
    "ToolCallData",
    "StreamChunk",
    "StreamEvent",
    # Exceptions
    "TantraError",
    "ProviderError",
    "ToolError",
    "ToolNotFoundError",
    "ToolValidationError",
    "ToolExecutionError",
    "ConfigurationError",
    "MaxIterationsError",
    "MCPError",
    "MCPConnectionError",
    "MCPToolExecutionError",
    "ContextMergeConflictError",
    # Checkpoints
    "Checkpoint",
    "CheckpointStore",
    "PostgresCheckpointStore",
    # In-the-Loop (ITL)
    "Interrupt",
    "InterruptResponse",
    "InterruptHandler",
    "CallbackInterruptHandler",
    "AgentRegistry",
    "default_registry",
    "register_agent",
    "get_agent",
    "ExecutionInterruptedError",
    "AbortedError",
    # Warden Pattern
    "Warden",
    "WardenTool",
    "WardenPreview",
    "WardenToolSet",
    "warden_tool",
    # Deployment
    "DeploymentGate",
    "DeploymentResult",
    "DeploymentStatus",
    "PerformanceBaseline",
    "PerformanceMonitor",
    "DegradationThresholds",
    "BaselineStore",
    "FileBaselineStore",
    "deploy_with_gate",
    # Multi-Agent Orchestration
    "Orchestrator",
    "OrchestrationDetail",
    "AgentStep",
    "Pipeline",
    "Router",
    "Parallel",
    "chain",
    "fan_out",
    "select",
    # Solo
    "Solo",
    # Swarm (Dynamic Handoffs)
    "Swarm",
    "SwarmDetail",
    "SwarmStep",
    "Handoff",
    "swarm",
    # Serve (HTTP API)
    "RunnableServer",
    "serve",
    "RunnableFactory",
    "PostgresRunnableFactory",
    # Automation-First Rules
    "Rule",
    "RuleMatch",
    "RuleSet",
    "KeywordRule",
    "RegexRule",
    "LookupRule",
    "FunctionRule",
    "RejectRule",
    "ConditionalRule",
    # Retry/Recovery
    "RetryPolicy",
    "RetryResult",
    "RetryCallback",
    "LoggingRetryCallback",
    "BackoffStrategy",
    "RetryableError",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitOpenError",
    "retry_async",
    "retry_sync",
    "with_retry",
    # OpenTelemetry Instrumentation
    "instrument",
    "uninstrument",
    "is_instrumented",
    "get_tracer",
    "get_meter",
    "span",
    "SpanAttributes",
    "trace_agent_run",
    "trace_llm_call",
    "trace_llm_stream",
    "trace_tool_call",
    "trace_orchestration_run",
    "trace_swarm_run",
    "trace_graph_run",
    "record_agent_run",
    "record_llm_call",
    "record_tool_call",
    "record_rate_limit",
    "record_orchestration_run",
    "record_swarm_handoff",
    "record_graph_node",
    "record_rule_evaluation",
    "record_error",
    # Advanced Graph Orchestration
    "Graph",
    "GraphBuilder",
    "GraphState",
    "GraphDetail",
    "Node",
    "AgentNode",
    "RouterNode",
    "FunctionNode",
    "Edge",
    "EdgeCondition",
    "NodeType",
    "create_graph",
]
