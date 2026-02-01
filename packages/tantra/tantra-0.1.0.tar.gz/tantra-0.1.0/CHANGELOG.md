# Changelog

All notable changes to Tantra are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-15

### Added

- **Agent**: Core `Agent` class with async-first API (`run()`, `run_sync()`, `stream()`, `stream_events()`), builder methods (`with_tools()`, `with_system_prompt()`, `with_hooks()`, etc.), and `clone()` for session isolation.
- **Tools**: `@tool` decorator with auto-generated JSON schemas from type hints and docstrings. `ToolSet` for grouping tools. Support for async tools and `RunContext` injection.
- **Memory**: `Memory` ABC with `ConversationMemory` (unbounded) and `WindowedMemory` (last N messages) implementations.
- **Providers**: `ModelProvider` ABC with built-in implementations for OpenAI (`OpenAIProvider`), Anthropic (`AnthropicProvider`), and Ollama (`OllamaProvider`). Provider string parsing (`"openai:gpt-4o"`).
- **Evaluation**: `EvalSuite` and `EvalCase` for testing agent behavior. Built-in matchers: `contains`, `not_contains`, `matches_regex`, `json_valid`, `json_schema`, `tool_called`, `tool_not_called`, `cost_under`, `tokens_under`, `custom`.
- **Observability**: `Logger` and `CostTracker` for structured logging and cost estimation. Every `RunResult` includes a complete execution trace with `LogEntry` objects.
- **In-the-Loop**: `@tool(interrupt="...")` for human approval gates. `InterruptHandler` ABC with `CLIInterruptHandler` and `CallbackInterruptHandler`. Async checkpoint-based interrupts with `CheckpointStore` (`MemoryCheckpointStore`, `SQLiteCheckpointStore`). `AgentRegistry` for multi-agent checkpoint resolution.
- **Warden Pattern**: `@warden_tool` decorator for sandboxed execution with preview. `Warden` class for review workflows. `WardenToolSet` and `WardenPreview` for structured preview data.
- **Rules**: Automation-First pattern with `RuleSet` and `Rule` ABC. Built-in rules: `KeywordRule`, `RegexRule`, `LookupRule`, `FunctionRule`, `RejectRule`, `ConditionalRule`. Rules are checked before the LLM for zero-cost instant responses.
- **Orchestration**: Multi-agent patterns:
    - `Pipeline` / `chain()` -- Sequential execution with output flowing between agents.
    - `Router` / `select()` -- Conditional routing to specialized agents.
    - `Parallel` / `fan_out()` -- Concurrent execution with combined results.
    - `Supervisor` -- Coordinator agent delegates to worker agents.
    - `Graph` / `GraphBuilder` / `create_graph()` -- Graph-based workflows with conditional edges, `AgentNode`, `FunctionNode`, `RouterNode`.
    - `Swarm` / `swarm()` -- Dynamic agent handoffs with context preservation via `Handoff` tool.
    - `ReActAgent` / `react()` -- Reason + Act pattern for step-by-step reasoning.
- **Resilience**:
    - `RetryPolicy` with configurable `BackoffStrategy` (constant, linear, exponential, exponential with jitter). `retry_async()`, `retry_sync()`, `@with_retry` decorator. `RetryCallback` and `LoggingRetryCallback`.
    - `CircuitBreaker` with `CircuitBreakerConfig` (failure threshold, recovery timeout, success threshold). Context manager and `@protect` decorator.
    - `RateLimiter` with `RateLimitConfig`. Built-in presets: `OPENAI_TIER1`, `OPENAI_TIER2`, `OPENAI_TIER3`, `ANTHROPIC_TIER1`, `ANTHROPIC_TIER2`.
- **OpenTelemetry**: `instrument()` / `uninstrument()` for distributed tracing and metrics. Automatic spans for agent runs, LLM calls, and tool executions. Custom `span()` context manager. Metric recording functions for agent runs, LLM calls, tool calls, rule evaluations, errors, orchestration runs, swarm handoffs, and graph nodes.
- **Serve**: `AgentServer` and `serve()` for exposing agents as HTTP APIs with health checks and session management.
- **MCP**: `MCPTools` for integrating Model Context Protocol tool servers.
- **RunContext**: Shared mutable key-value store for tool-to-tool data sharing. `ContextStore` ABC with `MemoryContextStore`. Session-based persistence via `session_id`.
- **RunHooks**: Lifecycle hooks for agent runs (`on_run_start`, `on_run_end`, `on_run_error`, `on_tool_call`, `on_tool_result`) and orchestration runs (`on_orchestration_start`, `on_orchestration_end`, `on_orchestration_error`).
- **Deployment**: `DeploymentGate` for evaluation-gated deployment. `PerformanceBaseline` and `PerformanceMonitor` for degradation detection. `DegradationThresholds` for configurable alerting. `deploy_with_gate()` convenience function.
- **Retriever**: `Retriever` ABC for RAG with `InMemoryRetriever` for development and `Document` data class.
- **Multimodal**: `ImageContent`, `FileContent`, `TextContent`, and `ContentBlock` types for sending images and files to vision-capable models.
- **Exceptions**: Full error hierarchy: `TantraError`, `ProviderError`, `ToolError`, `ToolNotFoundError`, `ToolValidationError`, `ToolExecutionError`, `ConfigurationError`, `MaxIterationsError`, `MCPError`, `MCPConnectionError`, `MCPToolExecutionError`, `ContextMergeConflictError`.
