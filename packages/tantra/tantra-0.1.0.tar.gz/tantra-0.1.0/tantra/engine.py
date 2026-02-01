"""Execution engine for Tantra agents.

This module contains the internal execution logic that drives agent runs.
It handles the main loop of LLM calls, tool execution, and logging.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from uuid import UUID, uuid4

from .checkpoints import Checkpoint, CheckpointStore
from .context import RunContext
from .exceptions import ConfigurationError, MaxIterationsError
from .hooks import RunHooks, _invoke_hooks
from .intheloop import (
    Interrupt,
    InterruptHandler,
    InterruptResponse,
    Warden,
    WardenTool,
)
from .memory import ConversationMemory, Memory
from .observability import CostTracker, Logger, create_run_metadata
from .providers.base import ModelProvider
from .tools import ToolDefinition, ToolSet
from .types import (
    ContentBlock,
    FileContent,
    ImageContent,
    LogType,
    Message,
    RunResult,
    StreamChunk,
    StreamEvent,
    TextContent,
    ToolCallData,
)


class ExecutionInterruptedError(Exception):
    """Raised when execution is interrupted and waiting for human input."""

    def __init__(self, checkpoint_id: str, prompt: str):
        """Initialize ExecutionInterruptedError.

        Args:
            checkpoint_id: The ID of the checkpoint where execution paused.
            prompt: The prompt message displayed to the human for input.
        """
        self.checkpoint_id = checkpoint_id
        self.prompt = prompt
        super().__init__(f"Execution paused. Checkpoint: {checkpoint_id}")


class AbortedError(Exception):
    """Raised when execution is aborted by human."""

    def __init__(self, reason: str | None = None):
        """Initialize AbortedError.

        Args:
            reason: Optional explanation of why execution was aborted.
        """
        self.reason = reason
        super().__init__(f"Execution aborted: {reason or 'No reason provided'}")


class ExecutionEngine:
    """Internal engine that executes agent runs.

    Handles the main execution loop:
    1. Build messages from system prompt + memory + user input
    2. Call LLM provider
    3. Process tool calls if any (with interrupt handling)
    4. Repeat until final response or max iterations
    5. Return result with full trace
    """

    def __init__(
        self,
        provider: ModelProvider,
        tools: ToolSet | None = None,
        system_prompt: str = "",
        memory: Memory | None = None,
        max_iterations: int = 10,
        interrupt_handler: InterruptHandler | None = None,
        checkpoint_store: CheckpointStore | None = None,
        name: str | None = None,
        warden: Warden | None = None,
        parallel_tool_execution: bool = True,
        hooks: list[RunHooks] | None = None,
    ):
        """Initialize the ExecutionEngine.

        Args:
            provider: The LLM provider used for completions.
            tools: Optional set of tools available to the agent.
            system_prompt: System prompt prepended to every LLM call.
            memory: Conversation memory implementation. Defaults to
                ConversationMemory.
            max_iterations: Maximum LLM call iterations before raising
                MaxIterationsError.
            interrupt_handler: Optional handler for in-the-loop
                interrupts. When set, the handler is notified before the
                engine checkpoints and raises ExecutionInterruptedError.
                Resumption is always explicit via ``resume()``.
            checkpoint_store: Store for persisting execution checkpoints.
                Required when using interrupt or resume functionality.
            name: Human-readable name for this agent, used in checkpoints and
                interrupts.
            warden: Optional Warden for reviewing tool calls that require
                approval via the Warden pattern.
            parallel_tool_execution: Whether to execute independent tool
                calls concurrently. Defaults to True.
            hooks: Optional list of RunHooks for lifecycle callbacks.
        """
        self.provider = provider
        self.tools = tools
        self.system_prompt = system_prompt
        self.memory = memory or ConversationMemory()
        self.max_iterations = max_iterations
        self.interrupt_handler = interrupt_handler
        self.checkpoint_store = checkpoint_store
        self.name = name or "default"
        self.warden = warden
        self.parallel_tool_execution = parallel_tool_execution
        self.hooks: list[RunHooks] = hooks or []
        self.context: RunContext | None = None

    async def run(
        self,
        user_input: str,
        *,
        attachments: list[ImageContent | FileContent] | None = None,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        logger: Logger | None = None,
        on_event: Any | None = None,
    ) -> RunResult:
        """Execute a full agent run.

        Args:
            user_input: The user's input message.
            attachments: Optional list of image or file attachments to
                include with the user message.
            run_id: Optional run ID (auto-generated if not provided).
            parent_run_id: Optional parent run ID for multi-agent trace correlation.
            logger: Optional logger for observability.
            on_event: Optional async callback for streaming events. When
                provided, the engine uses the provider's streaming API and
                emits StreamEvent objects (token, tool_call, tool_result).

        Returns:
            RunResult with output, trace, and metadata.

        Raises:
            MaxIterationsError: If max_iterations is exceeded.
            ProviderError: If the LLM provider fails.
            ToolExecutionError: If a tool fails during execution.
            ExecutionInterruptedError: If execution is paused waiting for
                human input (async checkpoint mode).
            AbortedError: If a human aborted execution via an interrupt.
        """
        run_id = run_id or uuid4()
        logger = logger or Logger(run_id=run_id, parent_run_id=parent_run_id)
        cost_tracker = CostTracker(model=self.provider.model_name)
        logger.start_run()

        if on_event is not None:
            logger.log(LogType.PROMPT, data={"input": user_input, "streaming": True})

        # Add user message to memory
        user_message = self._build_user_message(user_input, attachments)
        self.memory.add_message(user_message)

        try:
            final_output, iterations, tool_calls_count = await self._execute_loop(
                logger=logger,
                cost_tracker=cost_tracker,
                run_id=run_id,
                on_event=on_event,
            )
        except Exception as e:
            error_ctx = "agent_run_streaming" if on_event is not None else "agent_run"
            logger.log_error(e, context=error_ctx)
            raise

        # Build result
        metadata = create_run_metadata(
            run_id=run_id,
            cost_tracker=cost_tracker,
            duration_ms=logger.get_duration_ms(),
            tool_calls_count=tool_calls_count,
            iterations=iterations,
        )

        return RunResult(
            output=final_output,
            trace=logger.entries,
            metadata=metadata,
        )

    async def _execute_loop(
        self,
        *,
        logger: Logger,
        cost_tracker: CostTracker,
        run_id: UUID,
        on_event: Any | None = None,
    ) -> tuple[str, int, int]:
        """Execute the main LLM iteration loop.

        Shared by ``run()`` and ``resume()``.  Repeatedly calls the LLM
        provider, processes tool calls, and loops until a final text
        response or max iterations.  When *on_event* is provided, uses
        the provider's streaming API and emits token / tool events.

        Args:
            logger: Logger for observability.
            cost_tracker: Tracks token usage and cost.
            run_id: Current run identifier.
            on_event: Optional async callback for streaming events.

        Returns:
            Tuple of ``(final_output, iterations, tool_calls_count)``.

        Raises:
            MaxIterationsError: If max_iterations is exceeded.
        """
        iterations = 0
        tool_calls_count = 0
        final_output = ""

        while iterations < self.max_iterations:
            iterations += 1
            logger.set_iteration(iterations)

            messages = self._build_messages()
            tool_schemas = self.tools.get_schemas() if self.tools else None

            if on_event is not None:
                # ── streaming: use provider streaming API ────────────
                accumulated_content = ""
                final_chunk: StreamChunk | None = None
                stream_start = time.time()

                async for chunk in self.provider.complete_stream(
                    messages, tools=tool_schemas
                ):
                    if chunk.content:
                        accumulated_content += chunk.content
                        await on_event(StreamEvent("token", {"token": chunk.content}))
                    if chunk.is_final:
                        final_chunk = chunk

                stream_duration_ms = (time.time() - stream_start) * 1000

                logger.log(
                    LogType.LLM_RESPONSE,
                    data={
                        "content_length": len(accumulated_content),
                        "tool_calls": [tc.model_dump() for tc in final_chunk.tool_calls]
                        if final_chunk and final_chunk.tool_calls
                        else None,
                        "streaming": True,
                    },
                    metadata={"duration_ms": stream_duration_ms},
                )

                tool_calls = (
                    final_chunk.tool_calls
                    if final_chunk and final_chunk.tool_calls
                    else None
                )
                content = accumulated_content
            else:
                # ── non-streaming: blocking provider call ───────────
                logger.log_prompt([m.model_dump() for m in messages])

                llm_start = time.time()
                response = await self.provider.complete(messages, tools=tool_schemas)
                llm_duration_ms = (time.time() - llm_start) * 1000

                cost_tracker.add_tokens(response.prompt_tokens, response.completion_tokens)

                logger.log_llm_response(
                    content=response.content,
                    tool_calls=[tc.model_dump() for tc in response.tool_calls]
                    if response.tool_calls
                    else None,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    duration_ms=llm_duration_ms,
                )

                tool_calls = response.tool_calls if response.tool_calls else None
                content = response.content or ""

            # ── unified tool / response handling ────────────────
            if tool_calls and self.tools:
                await self._process_tool_calls(
                    tool_calls, logger, run_id, on_event=on_event
                )
                tool_calls_count += len(tool_calls)
            else:
                final_output = content
                self.memory.add_message(Message(role="assistant", content=final_output))
                logger.log_final_response(final_output)
                break
        else:
            raise MaxIterationsError(self.max_iterations)

        return final_output, iterations, tool_calls_count

    async def resume(
        self,
        checkpoint_id: str,
        response: InterruptResponse,
        logger: Logger | None = None,
        on_event: Any | None = None,
    ) -> RunResult:
        """Resume execution from a checkpoint after human input.

        Args:
            checkpoint_id: The checkpoint to resume from.
            response: The human's response.
            logger: Optional logger.

        Returns:
            RunResult with output, trace, and metadata.

        Raises:
            ValueError: If the checkpoint is not found or is not in
                ``pending`` status.
            AbortedError: If the human chose not to proceed.
            MaxIterationsError: If max_iterations is exceeded after
                resuming.
        """
        # Ensure checkpoint store is configured
        if self.checkpoint_store is None:
            raise ConfigurationError("checkpoint_store required for interrupt/resume")

        # Load checkpoint
        checkpoint = await self.checkpoint_store.load(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        if checkpoint.status != "pending":
            raise ValueError(f"Checkpoint is not pending: {checkpoint.status}")

        run_id = checkpoint.run_id
        logger = logger or Logger(run_id=run_id)
        cost_tracker = CostTracker(model=self.provider.model_name)

        logger.start_run()

        # Restore memory from checkpoint
        self.memory.clear()
        for msg in checkpoint.messages:
            self.memory.add_message(msg)

        # Handle the response
        if not response.proceed:
            # Human aborted
            await self.checkpoint_store.update(
                checkpoint_id,
                status="aborted",
                response_reason=response.reason,
            )
            raise AbortedError(response.reason)

        # Execute the pending tool with approval
        tool_name = checkpoint.pending_tool
        tool_args = checkpoint.pending_args

        if on_event is not None:
            await on_event(StreamEvent("tool_call", {
                "tool": tool_name, "args": tool_args,
            }))

        start_time = time.time()
        try:
            result = await self.tools.execute(tool_name, tool_args, context=self.context)
            result_str = self._serialize_tool_result(result)
        except Exception as e:
            result_str = f"Error: {e}"
            logger.log_error(e, context=f"tool:{tool_name}")

        duration_ms = (time.time() - start_time) * 1000

        if on_event is not None:
            await on_event(StreamEvent("tool_result", {
                "tool": tool_name, "result": result_str[:500],
                "duration_ms": duration_ms,
            }))

        # Log the tool result
        logger.log_tool_result(tool_name, result_str, duration_ms)

        # Add tool response to memory
        self.memory.add_message(
            Message(role="tool", content=result_str, tool_call_id=checkpoint.pending_tool_call_id)
        )

        # Mark checkpoint as completed
        await self.checkpoint_store.update(
            checkpoint_id,
            status="completed",
            response_value=response.value,
        )

        # Continue execution from here
        try:
            final_output, iterations, loop_tool_calls = await self._execute_loop(
                logger=logger,
                cost_tracker=cost_tracker,
                run_id=run_id,
                on_event=on_event,
            )
        except Exception as e:
            logger.log_error(e, context="agent_resume")
            raise

        metadata = create_run_metadata(
            run_id=run_id,
            cost_tracker=cost_tracker,
            duration_ms=logger.get_duration_ms(),
            tool_calls_count=1 + loop_tool_calls,  # +1 for the pending tool
            iterations=iterations,
        )

        return RunResult(
            output=final_output,
            trace=logger.entries,
            metadata=metadata,
        )

    async def _process_tool_calls(
        self,
        tool_calls: list[ToolCallData],
        logger: Logger,
        run_id: UUID,
        on_event: Any | None = None,
    ) -> None:
        """Process a list of tool calls from the LLM.

        Executes tools and adds results to memory. When parallel_tool_execution
        is enabled, consecutive parallel-safe tools run concurrently.
        Tools requiring interrupts or warden review run sequentially.

        Order is preserved: [A, B, C(sequential), D, E] executes as:
        - Parallel batch [A, B]
        - Sequential C
        - Parallel batch [D, E]

        Args:
            tool_calls: The list of tool calls returned by the LLM.
            logger: Logger for recording tool execution events.
            run_id: The current run identifier.

        Raises:
            ExecutionInterruptedError: If a tool requires an interrupt and
                no interrupt_handler is configured (async checkpoint mode).
            AbortedError: If a human rejects execution via the warden or
                interrupt handler.
        """
        # Add assistant message with tool calls FIRST (before tool responses)
        self.memory.add_message(Message(role="assistant", content=None, tool_calls=tool_calls))

        # Process tools in order, batching consecutive parallel-safe tools
        parallel_batch: list[ToolCallData] = []

        for tc in tool_calls:
            tool_def = self.tools.get(tc.name)
            needs_sequential = tool_def.requires_interrupt or (
                isinstance(tool_def, WardenTool) and self.warden
            )

            if needs_sequential or not self.parallel_tool_execution:
                # Flush any accumulated parallel batch first
                if parallel_batch:
                    await self._execute_tools_parallel(
                        parallel_batch, logger, run_id, on_event=on_event
                    )
                    parallel_batch = []
                # Then execute this sequential tool
                await self._execute_tool_sequential(tc, logger, run_id, on_event=on_event)
            else:
                # Accumulate parallel-safe tools
                parallel_batch.append(tc)

        # Flush any remaining parallel batch
        if parallel_batch:
            await self._execute_tools_parallel(parallel_batch, logger, run_id, on_event=on_event)

    async def _execute_tools_parallel(
        self,
        tool_calls: list[ToolCallData],
        logger: Logger,
        run_id: UUID | None = None,
        on_event: Any | None = None,
    ) -> None:
        """Execute multiple tools concurrently using asyncio.gather.

        All tool calls are started simultaneously. Results are logged and
        added to memory in the original call order after all complete.

        Args:
            tool_calls: The batch of tool calls to execute in parallel.
            logger: Logger for recording tool execution events.
            run_id: Optional run identifier for hook callbacks.
        """
        # Log and emit all tool calls first
        for tc in tool_calls:
            logger.log_tool_call(tc.name, tc.arguments)
            if on_event is not None:
                await on_event(
                    StreamEvent("tool_call", {"tool": tc.name, "args": tc.arguments})
                )

        # Create tasks for all tools
        async def execute_one(tc: ToolCallData) -> tuple[ToolCallData, str, float]:
            if self.hooks:
                await _invoke_hooks(
                    self.hooks,
                    "on_tool_call",
                    run_id=run_id,
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    context=self.context,
                )
            start_time = time.time()
            try:
                result = await self.tools.execute(tc.name, tc.arguments, context=self.context)
                result_str = self._serialize_tool_result(result)
            except Exception as e:
                result_str = f"Error: {e}"
                logger.log_error(e, context=f"tool:{tc.name}")
            duration_ms = (time.time() - start_time) * 1000
            if self.hooks:
                await _invoke_hooks(
                    self.hooks,
                    "on_tool_result",
                    run_id=run_id,
                    tool_name=tc.name,
                    result=result_str,
                    duration_ms=duration_ms,
                    context=self.context,
                )
            return tc, result_str, duration_ms

        # Run all tools concurrently
        tasks = [asyncio.create_task(execute_one(tc)) for tc in tool_calls]
        results = await asyncio.gather(*tasks)

        # Log results and add to memory (in original order)
        for tc, result_str, duration_ms in results:
            logger.log_tool_result(tc.name, result_str, duration_ms)
            if on_event is not None:
                await on_event(
                    StreamEvent(
                        "tool_result",
                        {"tool": tc.name, "result": result_str, "duration_ms": duration_ms},
                    )
                )
            self.memory.add_message(Message(role="tool", content=result_str, tool_call_id=tc.id))

    async def _execute_tool_sequential(
        self,
        tc: ToolCallData,
        logger: Logger,
        run_id: UUID,
        on_event: Any | None = None,
    ) -> None:
        """Execute a single tool that requires sequential processing.

        Handles Warden-reviewed tools, interrupt-gated tools, and regular
        tools that were flagged for sequential execution. The tool result
        is logged and added to conversation memory.

        Args:
            tc: The tool call data from the LLM response.
            logger: Logger for recording tool execution events.
            run_id: The current run identifier.

        Raises:
            ExecutionInterruptedError: If the tool requires an interrupt
                and no interrupt_handler is configured.
        """
        logger.log_tool_call(tc.name, tc.arguments)

        tool_def = self.tools.get(tc.name)

        # Warden tools get preview + review
        if isinstance(tool_def, WardenTool) and self.warden:
            auto_approved, preview = await self.warden.review(tool_def, tc.arguments)

            # Log warden review request with full preview context
            logger.log(
                LogType.TOOL_CALL,
                data={
                    "tool": tc.name,
                    "arguments": tc.arguments,
                    "warden_review": True,
                    "preview": {
                        "description": preview.description,
                        "preview_result": str(preview.preview_result)[:500],
                        "risks": preview.risks,
                        "reversible": preview.reversible,
                    },
                },
            )

            if not auto_approved:
                # Not auto-approved: notify, checkpoint, raise
                prompt = self.warden._build_prompt(preview)
                if self.warden.handler:
                    interrupt = Interrupt(
                        id=f"warden-{tool_def.name}-{run_id}",
                        run_id=run_id,
                        name=self.name,
                        prompt=prompt,
                        tool_name=tc.name,
                        tool_args=tc.arguments,
                        context={
                            "preview_result": str(preview.preview_result),
                            "risks": preview.risks,
                            "reversible": preview.reversible,
                            "warden": True,
                        },
                    )
                    await self.warden.handler.notify(interrupt)

                # Log that warden needs human review
                logger.log(
                    LogType.TOOL_RESULT,
                    data={
                        "tool": tc.name,
                        "warden_decision": "pending_review",
                        "preview_description": preview.description,
                        "risks": preview.risks,
                        "reversible": preview.reversible,
                    },
                    metadata={"warden_review": True},
                )

                checkpoint = await self._create_checkpoint(tool_def, tc, run_id, prompt=prompt)
                raise ExecutionInterruptedError(checkpoint.id, prompt)

            # Auto-approved — log and continue to execution
            logger.log(
                LogType.TOOL_RESULT,
                data={
                    "tool": tc.name,
                    "warden_decision": "auto_approved",
                    "preview_description": preview.description,
                    "risks": preview.risks,
                    "reversible": preview.reversible,
                },
                metadata={"warden_review": True},
            )

        # Regular interrupt handling
        elif tool_def.requires_interrupt:
            if self.interrupt_handler:
                interrupt = Interrupt(
                    id=str(uuid4()),
                    run_id=run_id,
                    name=self.name,
                    prompt=tool_def.interrupt,
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    context={
                        "messages_count": len(self.memory.get_messages()),
                    },
                )
                await self.interrupt_handler.notify(interrupt)
            checkpoint = await self._create_checkpoint(tool_def, tc, run_id)
            raise ExecutionInterruptedError(checkpoint.id, tool_def.interrupt)

        # Emit tool_call event (after gates, before execution)
        if on_event is not None:
            await on_event(
                StreamEvent("tool_call", {"tool": tc.name, "args": tc.arguments})
            )

        # Execute the tool
        if self.hooks:
            await _invoke_hooks(
                self.hooks,
                "on_tool_call",
                run_id=run_id,
                tool_name=tc.name,
                arguments=tc.arguments,
                context=self.context,
            )
        start_time = time.time()
        try:
            result = await self.tools.execute(
                tc.name,
                tc.arguments,
                context=self.context,
            )
            result_str = self._serialize_tool_result(result)
        except Exception as e:
            result_str = f"Error: {e}"
            logger.log_error(e, context=f"tool:{tc.name}")

        duration_ms = (time.time() - start_time) * 1000
        if self.hooks:
            await _invoke_hooks(
                self.hooks,
                "on_tool_result",
                run_id=run_id,
                tool_name=tc.name,
                result=result_str,
                duration_ms=duration_ms,
                context=self.context,
            )
        logger.log_tool_result(tc.name, result_str, duration_ms)
        if on_event is not None:
            await on_event(
                StreamEvent(
                    "tool_result",
                    {"tool": tc.name, "result": result_str, "duration_ms": duration_ms},
                )
            )
        self.memory.add_message(Message(role="tool", content=result_str, tool_call_id=tc.id))

    async def _create_checkpoint(
        self,
        tool_def: ToolDefinition,
        tool_call: ToolCallData,
        run_id: UUID,
        prompt: str | None = None,
    ) -> Checkpoint:
        """Create and persist a checkpoint for async interrupt handling.

        Captures the current conversation state so execution can be
        resumed later via ``resume()`` after the human responds.

        Args:
            tool_def: The tool definition that triggered the interrupt.
            tool_call: The tool call data from the LLM response.
            run_id: The current run identifier.
            prompt: Optional explicit prompt. Defaults to ``tool_def.interrupt``.

        Returns:
            The saved Checkpoint instance.

        Raises:
            ConfigurationError: If no checkpoint_store is configured.
        """
        if self.checkpoint_store is None:
            raise ConfigurationError("checkpoint_store required for interrupt/resume")

        checkpoint = Checkpoint(
            run_id=run_id,
            name=self.name,
            messages=self.memory.get_messages(),
            pending_tool=tool_call.name,
            pending_args=tool_call.arguments,
            pending_tool_call_id=tool_call.id,
            prompt=prompt or tool_def.interrupt,
            context={},
        )

        await self.checkpoint_store.save(checkpoint)
        return checkpoint

    def _build_messages(self) -> list[Message]:
        """Build the full message list for an LLM call.

        Prepends the system prompt (if configured) to the conversation
        history stored in memory.

        Returns:
            Ordered list of Messages starting with the system prompt
            followed by all messages from memory.
        """
        messages = []

        # System prompt first
        if self.system_prompt:
            messages.append(Message(role="system", content=self.system_prompt))

        # Then memory messages
        messages.extend(self.memory.get_messages())

        return messages

    def _build_user_message(
        self,
        user_input: str,
        attachments: list[ImageContent | FileContent] | None = None,
    ) -> Message:
        """Build a user Message, optionally with image or file attachments.

        If attachments are provided, content becomes a list of ContentBlocks
        (TextContent followed by the attachments). Otherwise, content is a
        plain string, preserving existing behaviour.

        Args:
            user_input: The user's text input.
            attachments: Optional list of ImageContent or FileContent
                objects to attach to the message.

        Returns:
            A Message with role ``user`` and the appropriate content.
        """
        if attachments:
            content_blocks: list[ContentBlock] = [TextContent(text=user_input), *attachments]
            return Message(role="user", content=content_blocks)
        return Message(role="user", content=user_input)

    def _serialize_tool_result(self, result: Any) -> str:
        """Convert a tool result to a string suitable for the LLM.

        Strings are returned as-is. Other types are serialized via
        ``json.dumps``; if JSON serialization fails, ``str()`` is used
        as a fallback.

        Args:
            result: The raw return value from tool execution.

        Returns:
            A string representation of the tool result.
        """
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result)
        except (TypeError, ValueError):
            return str(result)
