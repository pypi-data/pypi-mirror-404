"""Agent class for Tantra.

The Agent is the primary interface for developers using Tantra.
It provides a simple, declarative API for creating and running AI agents.
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID, uuid4

from .checkpoints import CheckpointStore
from .context import ContextStore, MemoryContextStore, RunContext
from .engine import ExecutionEngine
from .exceptions import ConfigurationError
from .hooks import RunHooks, _invoke_hooks
from .intheloop import (
    InterruptHandler,
    InterruptResponse,
    Warden,
)
from .memory import ConversationMemory, Memory
from .observability import trace_agent_run
from .providers import parse_model_string
from .providers.base import ModelProvider
from .rules import Rule, RuleSet
from .tools import ToolSet
from .types import FileContent, ImageContent, LogType, RunMetadata, RunResult

_UNSET: Any = object()


def _run_sync(coro: Any) -> Any:
    """Run a coroutine synchronously, handling existing event loops.

    Args:
        coro: The coroutine to execute.

    Returns:
        The coroutine's return value.

    Raises:
        RuntimeError: If called from an async context without nest_asyncio installed.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)

    # Already in async context - use nest_asyncio
    import nest_asyncio

    nest_asyncio.apply()
    return asyncio.run(coro)


class Agent:
    """An AI agent that can use tools and maintain conversation history.

    The Agent class is the main entry point for using Tantra. It wraps the
    execution engine and provides a clean, async-first API.

    Examples:
        ```python
        # Simple agent without tools
        agent = Agent("openai:gpt-4o", system_prompt="You are a helpful assistant.")
        result = await agent.run("Hello!")
        print(result.output)

        # Agent with tools
        @tool
        def get_weather(city: str) -> str:
            return f"Weather in {city}: Sunny, 72F"

        agent = Agent(
            "openai:gpt-4o",
            tools=ToolSet([get_weather]),
            system_prompt="You can check the weather for users."
        )
        result = await agent.run("What's the weather in Tokyo?")

        # Agent with in-the-loop (interrupt tools always checkpoint + raise)
        @tool(interrupt="Approve this refund?")
        def process_refund(amount: float) -> str:
            return f"Refunded ${amount}"

        agent = Agent(
            "openai:gpt-4o",
            tools=ToolSet([process_refund]),
        )
        try:
            result = await agent.run("Refund $50 to the customer")
        except ExecutionInterruptedError as e:
            # Get human approval, then resume
            result = await agent.resume(
                e.checkpoint_id,
                InterruptResponse(value=True, proceed=True),
            )
        ```
    """

    def __init__(
        self,
        provider: ModelProvider | str,
        tools: ToolSet | None = None,
        system_prompt: str = "",
        memory: Memory | None = None,
        max_iterations: int = 10,
        interrupt_handler: InterruptHandler | None = None,
        checkpoint_store: CheckpointStore | None = None,
        name: str | None = None,
        warden: Warden | None = None,
        rules: list[Rule] | RuleSet | None = None,
        parallel_tool_execution: bool = True,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
    ):
        """Initialize an Agent.

        Args:
            provider: Either a ModelProvider instance or a string like "openai:gpt-4o".
                     If a string, it will be parsed to create the appropriate provider.
            tools: Optional ToolSet containing tools the agent can use.
            system_prompt: The system prompt that defines the agent's behavior.
            memory: Optional Memory instance for conversation history.
                   Defaults to ConversationMemory if not provided.
            max_iterations: Maximum number of LLM calls per run (prevents infinite loops).
                           Default is 10.
            interrupt_handler: Optional handler for in-the-loop interrupt
                              notifications. When set, the handler's ``notify()`` method
                              is called before checkpointing. Execution always raises
                              ``ExecutionInterruptedError``; resume via ``agent.resume()``.
            checkpoint_store: Optional store for persisting checkpoints.
                             Required when using interrupt or resume functionality.
            name: Optional human-readable name for this agent. Used for routing,
                 serve, and observability. Must be unique within a factory.
            warden: Optional Warden for sandboxed execution with preview/review.
                   When set, warden tools will show previews before execution.
            rules: Optional rules for automation-first pattern. Rules are checked
                  before calling the LLM. If a rule matches, its response is
                  returned immediately without any LLM cost.
            parallel_tool_execution: Whether to execute independent tools in parallel.
                                    Default True. Tools requiring interrupts or warden
                                    review always run sequentially.
            context_store: Optional store for persisting RunContext across runs.
                          Defaults to MemoryContextStore (in-memory).
                          Use with session_id in run() for cross-run context.
            hooks: Optional list of RunHooks for lifecycle callbacks.
                  Hooks fire at key execution points (run start/end, tool
                  call/result). They receive the RunContext and can inject
                  data for tools to consume.

        Raises:
            ConfigurationError: If provider string is invalid.
        """
        # Parse provider if string
        if isinstance(provider, str):
            try:
                self._provider = parse_model_string(provider)
            except ValueError as e:
                raise ConfigurationError(str(e))
        else:
            self._provider = provider

        self._tools = tools
        self._system_prompt = system_prompt
        self._memory = memory or ConversationMemory()
        self._max_iterations = max_iterations
        self._interrupt_handler = interrupt_handler
        self._checkpoint_store = checkpoint_store
        self._name = name
        self._warden = warden

        # Setup rules
        if rules is None:
            self._rules = RuleSet()
        elif isinstance(rules, RuleSet):
            self._rules = rules
        else:
            self._rules = RuleSet(rules)

        self._parallel_tool_execution = parallel_tool_execution
        self._context_store = context_store or MemoryContextStore()
        self._hooks: list[RunHooks] = list(hooks) if hooks else []

        # Create the execution engine
        self._engine = ExecutionEngine(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=self._memory,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            parallel_tool_execution=self._parallel_tool_execution,
            hooks=self._hooks,
        )

    @property
    def provider(self) -> ModelProvider:
        """The LLM provider used by this agent."""
        return self._provider

    @property
    def tools(self) -> ToolSet | None:
        """The tools available to this agent."""
        return self._tools

    @property
    def memory(self) -> Memory:
        """The memory used by this agent."""
        return self._memory

    @property
    def system_prompt(self) -> str:
        """The system prompt for this agent."""
        return self._system_prompt

    @property
    def name(self) -> str | None:
        """The agent's human-readable name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the agent's name."""
        self._name = value
        self._engine.name = value

    @property
    def max_iterations(self) -> int:
        """Maximum LLM calls per run."""
        return self._max_iterations

    @property
    def interrupt_handler(self) -> InterruptHandler | None:
        """The interrupt handler for in-the-loop."""
        return self._interrupt_handler

    @property
    def checkpoint_store(self) -> CheckpointStore | None:
        """The checkpoint store for persisting state."""
        return self._checkpoint_store

    @property
    def warden(self) -> Warden | None:
        """The Warden for sandboxed execution."""
        return self._warden

    @property
    def rules(self) -> RuleSet:
        """The rules for this agent."""
        return self._rules

    @property
    def parallel_tool_execution(self) -> bool:
        """Whether parallel tool execution is enabled."""
        return self._parallel_tool_execution

    @property
    def hooks(self) -> list[RunHooks]:
        """The lifecycle hooks for this agent."""
        return self._hooks

    @trace_agent_run
    async def run(
        self,
        user_input: str,
        *,
        attachments: list[ImageContent | FileContent] | None = None,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        session_id: str | None = None,
        context: RunContext | None = None,
        on_event: Any | None = None,
    ) -> RunResult:
        """Run the agent with the given input.

        This is the primary async method for invoking the agent. It returns
        when the agent has produced a final response.

        Args:
            user_input: The user's input message.
            attachments: Optional list of image attachments to include with the
                        user message. Images are sent as content blocks alongside
                        the text to vision-capable models.
            run_id: Optional unique identifier for this run.
            parent_run_id: Optional parent run ID for multi-agent trace correlation.
            session_id: Optional session ID for persisting RunContext across runs.
                       When provided, context is loaded from the context store at
                       the start and saved back after the run completes.
            context: Optional RunContext to use for this run. When provided,
                    this context is used directly instead of creating a fresh one.
                    Useful for sharing context across agents in orchestrations.
            on_event: Optional async callback for streaming events. When provided,
                     the engine uses the provider's streaming API and emits
                     StreamEvent objects (token, tool_call, tool_result) via this
                     callback. Used by orchestrators for unified event streaming.

        Returns:
            RunResult containing the output, execution trace, and metadata.

        Raises:
            MaxIterationsError: If the agent exceeds max_iterations.
            ProviderError: If the LLM provider fails.
            ToolExecutionError: If a tool fails.
            ExecutionInterruptedError: If a tool requires human approval and no handler is set.
            AbortedError: If a human rejected an action.
        """
        actual_run_id = run_id or uuid4()

        # Resolve RunContext: explicit > session load > fresh
        if context is not None:
            run_context = context
        elif session_id:
            saved_data = await self._context_store.load(session_id)
            run_context = RunContext(saved_data) if saved_data else RunContext()
        else:
            run_context = RunContext()

        # Check rules first (Automation-First / Tier 0)
        rule_match = self._rules.match(user_input)
        if rule_match:
            # Rule matched - return immediately without LLM call
            # Create trace entries for rule match
            from .observability import Logger

            logger = Logger(run_id=actual_run_id, parent_run_id=parent_run_id)
            logger.log(
                LogType.PROMPT,
                data={"input": user_input},
                metadata={"rule_evaluation": True},
            )
            logger.log(
                LogType.FINAL_RESPONSE,
                data={
                    "output": rule_match.response,
                    "handled_by_rule": True,
                    "rule_name": rule_match.rule_name,
                },
                metadata={"rule_match": True},
            )

            metadata = RunMetadata(
                run_id=actual_run_id,
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                estimated_cost=0.0,
                duration_ms=0.0,
                tool_calls_count=0,
                iterations=0,
            )

            # Save context if session
            if session_id:
                await self._context_store.save(session_id, run_context.to_dict())

            return RunResult(
                output=rule_match.response,
                trace=logger.entries,
                metadata=metadata,
                rule_match=rule_match,
                context=run_context,
            )

        # Set context on the engine for this run
        self._engine.context = run_context

        # Hook: on_run_start
        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_run_start",
                run_id=actual_run_id,
                user_input=user_input,
                name=self._name,
                context=run_context,
            )

        try:
            result = await self._engine.run(
                user_input,
                attachments=attachments,
                run_id=actual_run_id,
                parent_run_id=parent_run_id,
                on_event=on_event,
            )
        except Exception as exc:
            # Hook: on_run_error
            if self._hooks:
                await _invoke_hooks(
                    self._hooks,
                    "on_run_error",
                    run_id=actual_run_id,
                    error=exc,
                    context=run_context,
                )
            raise

        # Attach context to result
        result.context = run_context

        # Save context if session
        if session_id:
            await self._context_store.save(session_id, run_context.to_dict())

        # Hook: on_run_end
        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_run_end",
                run_id=actual_run_id,
                result=result,
                context=run_context,
            )

        return result

    def run_sync(
        self,
        user_input: str,
        *,
        attachments: list[ImageContent | FileContent] | None = None,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        session_id: str | None = None,
        context: RunContext | None = None,
    ) -> RunResult:
        """Run the agent synchronously.

        Convenience wrapper for non-async contexts.

        If called from within an existing event loop (e.g. Jupyter, async web
        frameworks), falls back to nest_asyncio if available.

        Args:
            user_input: The user's input message.
            attachments: Optional list of image attachments.
            run_id: Optional unique identifier for this run.
            parent_run_id: Optional parent run ID for multi-agent trace correlation.
            session_id: Optional session ID for context persistence.
            context: Optional RunContext to use for this run.

        Returns:
            RunResult containing the output, execution trace, and metadata.

        Raises:
            MaxIterationsError: If the agent exceeds max_iterations.
            ProviderError: If the LLM provider fails.
            ToolExecutionError: If a tool fails.
            ExecutionInterruptedError: If a tool requires human approval and no handler is set.
            AbortedError: If a human rejected an action.
            RuntimeError: If called from an async context without nest_asyncio.
        """
        return _run_sync(
            self.run(
                user_input,
                attachments=attachments,
                run_id=run_id,
                parent_run_id=parent_run_id,
                session_id=session_id,
                context=context,
            )
        )

    async def resume(
        self,
        checkpoint_id: str,
        response: InterruptResponse,
        on_event: Any | None = None,
    ) -> RunResult:
        """Resume execution from a checkpoint after human input.

        Use this when an agent run raised ExecutionInterruptedError and you have
        the human's response.

        Args:
            checkpoint_id: The checkpoint ID from ExecutionInterruptedError.
            response: The human's response.
            on_event: Optional async callback for streaming events.
                When provided, emits StreamEvent for tool executions.

        Returns:
            RunResult containing the output, execution trace, and metadata.

        Raises:
            ValueError: If checkpoint not found or not pending.
            AbortedError: If human rejected the action.

        Examples:
            ```python
            try:
                result = await agent.run("Delete user 123")
            except ExecutionInterruptedError as e:
                # Get human approval somehow
                approved = await ask_human(e.prompt)
                response = InterruptResponse(value=approved, proceed=approved)
                result = await agent.resume(e.checkpoint_id, response)
            ```
        """
        return await self._engine.resume(checkpoint_id, response, on_event=on_event)

    def resume_sync(
        self,
        checkpoint_id: str,
        response: InterruptResponse,
    ) -> RunResult:
        """Resume execution synchronously.

        Convenience sync wrapper around :meth:`resume`.

        Args:
            checkpoint_id: The checkpoint ID from ExecutionInterruptedError.
            response: The human's response.

        Returns:
            RunResult containing the output, execution trace, and metadata.

        Raises:
            ValueError: If checkpoint not found or not pending.
            AbortedError: If human rejected the action.
            RuntimeError: If called from an async context without nest_asyncio.
        """
        return _run_sync(self.resume(checkpoint_id, response))

    def clear_memory(self) -> None:
        """Clear the agent's conversation memory.

        Use this to start a fresh conversation without creating a new agent.
        """
        self._memory.clear()

    def with_tools(self, tools: ToolSet) -> Agent:
        """Create a new agent with additional/different tools.

        This creates a new Agent instance with the specified tools,
        sharing the same provider and configuration.

        Args:
            tools: The ToolSet to use.

        Returns:
            A new Agent instance with the specified tools.
        """
        return Agent(
            provider=self._provider,
            tools=tools,
            system_prompt=self._system_prompt,
            memory=None,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=self._rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def with_system_prompt(self, system_prompt: str) -> Agent:
        """Create a new agent with a different system prompt.

        Args:
            system_prompt: The new system prompt.

        Returns:
            A new Agent instance with the specified system prompt.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=system_prompt,
            memory=None,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=self._rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def with_interrupt_handler(self, handler: InterruptHandler) -> Agent:
        """Create a new agent with a different interrupt handler.

        Args:
            handler: The interrupt handler to use.

        Returns:
            A new Agent instance with the specified handler.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=self._memory,
            max_iterations=self._max_iterations,
            interrupt_handler=handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=self._rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def with_warden(self, warden: Warden) -> Agent:
        """Create a new agent with a Warden for sandboxed execution.

        Args:
            warden: The Warden to use for preview/review.

        Returns:
            A new Agent instance with the specified Warden.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=self._memory,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=warden,
            rules=self._rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def with_rules(self, rules: list[Rule] | RuleSet) -> Agent:
        """Create a new agent with different rules.

        Args:
            rules: The rules to use for Automation-First pattern.

        Returns:
            A new Agent instance with the specified rules.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=self._memory,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def with_parallel_tool_execution(self, enabled: bool = True) -> Agent:
        """Create a new agent with parallel tool execution setting.

        Args:
            enabled: Whether to execute independent tools in parallel.

        Returns:
            A new Agent instance with the specified setting.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=self._memory,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=self._rules,
            parallel_tool_execution=enabled,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def with_hooks(self, hooks: list[RunHooks]) -> Agent:
        """Create a new agent with different lifecycle hooks.

        Args:
            hooks: The lifecycle hooks to use.

        Returns:
            A new Agent instance with the specified hooks.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=self._memory,
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=self._rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=hooks,
        )

    def clone(
        self,
        *,
        memory: Memory | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ) -> Agent:
        """Create a copy of this agent with fresh memory and engine.

        Shares the same provider, tools, and configuration but creates
        an independent memory and execution engine. Useful for session
        isolation when serving agents over HTTP.

        Args:
            memory: Optional Memory instance for the clone. Defaults to
                   a fresh ConversationMemory.
            checkpoint_store: Optional CheckpointStore for the clone.
                   Defaults to reusing the original checkpoint store.

        Returns:
            A new Agent instance with isolated state.
        """
        return Agent(
            provider=self._provider,
            tools=self._tools,
            system_prompt=self._system_prompt,
            memory=memory or ConversationMemory(),
            max_iterations=self._max_iterations,
            interrupt_handler=self._interrupt_handler,
            checkpoint_store=checkpoint_store or self._checkpoint_store,
            name=self._name,
            warden=self._warden,
            rules=self._rules,
            parallel_tool_execution=self._parallel_tool_execution,
            context_store=self._context_store,
            hooks=self._hooks,
        )

    def clone_with(
        self,
        *,
        provider: ModelProvider | Any = _UNSET,
        tools: ToolSet | None | Any = _UNSET,
        system_prompt: str | Any = _UNSET,
        memory: Memory | None | Any = _UNSET,
        max_iterations: int | Any = _UNSET,
        interrupt_handler: InterruptHandler | None | Any = _UNSET,
        checkpoint_store: CheckpointStore | None | Any = _UNSET,
        name: str | None | Any = _UNSET,
        warden: Warden | None | Any = _UNSET,
        rules: list[Rule] | RuleSet | None | Any = _UNSET,
        parallel_tool_execution: bool | Any = _UNSET,
        context_store: ContextStore | None | Any = _UNSET,
        hooks: list[RunHooks] | None | Any = _UNSET,
    ) -> Agent:
        """Create a copy of this agent with specific field overrides.

        Any field not provided keeps the original agent's value.
        Unlike ``clone()``, this preserves the original memory by default
        instead of creating a fresh one.

        Args:
            provider: LLM provider override.
            tools: Tools override.
            system_prompt: System prompt override.
            memory: Memory override.
            max_iterations: Max iterations override.
            interrupt_handler: Interrupt handler override.
            checkpoint_store: Checkpoint store override.
            name: Agent name override.
            warden: Warden override.
            rules: Rules override.
            parallel_tool_execution: Parallel execution override.
            context_store: Context store override.
            hooks: Hooks override.

        Returns:
            A new Agent instance with the specified overrides applied.
        """
        return Agent(
            provider=provider if provider is not _UNSET else self._provider,
            tools=tools if tools is not _UNSET else self._tools,
            system_prompt=system_prompt if system_prompt is not _UNSET else self._system_prompt,
            memory=memory if memory is not _UNSET else self._memory,
            max_iterations=max_iterations if max_iterations is not _UNSET else self._max_iterations,
            interrupt_handler=interrupt_handler
            if interrupt_handler is not _UNSET
            else self._interrupt_handler,
            checkpoint_store=checkpoint_store
            if checkpoint_store is not _UNSET
            else self._checkpoint_store,
            name=name if name is not _UNSET else self._name,
            warden=warden if warden is not _UNSET else self._warden,
            rules=rules if rules is not _UNSET else self._rules,
            parallel_tool_execution=parallel_tool_execution
            if parallel_tool_execution is not _UNSET
            else self._parallel_tool_execution,
            context_store=context_store if context_store is not _UNSET else self._context_store,
            hooks=hooks if hooks is not _UNSET else self._hooks,
        )

    def __repr__(self) -> str:
        tool_count = len(self._tools) if self._tools else 0
        itl = "yes" if self._interrupt_handler else "no"
        return (
            f"Agent(model={self._provider.model_name!r}, "
            f"tools={tool_count}, "
            f"itl={itl}, "
            f"max_iterations={self._max_iterations})"
        )
