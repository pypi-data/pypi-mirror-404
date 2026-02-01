"""Swarm-style Agent Orchestration for Tantra.

Provides dynamic agent handoffs where agents can transfer control
to each other mid-conversation, preserving context.

Examples:
    ```python
    from tantra import Agent, Swarm

    triage = Agent("openai:gpt-4o", system_prompt="Route to appropriate agent")
    billing = Agent("openai:gpt-4o", system_prompt="Handle billing issues")
    support = Agent("openai:gpt-4o", system_prompt="Handle technical support")

    swarm = Swarm(
        agents={
            "triage": triage,
            "billing": billing,
            "support": support,
        },
        handoffs={
            "triage": ["billing", "support"],
            "billing": ["triage", "support"],
            "support": ["triage", "billing"],
        },
        entry_point="triage",
    )

    result = await swarm.run("I need help with my invoice")
    # triage -> billing (handoff) -> response
    ```
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ..checkpoints import Checkpoint, CheckpointStore
from ..context import ContextStore, MemoryContextStore, RunContext
from ..engine import ExecutionInterruptedError
from ..exceptions import ConfigurationError
from ..hooks import RunHooks, _invoke_hooks
from ..intheloop import InterruptResponse
from ..memory import ConversationMemory
from ..observability import Logger, trace_swarm_run
from ..tools import ToolDefinition, ToolSet
from ..types import LogEntry, LogType, RunMetadata, RunResult, StreamEvent
from .base import AgentStep, OrchestrationDetail, Orchestrator, resolve_context, save_context

_logger = logging.getLogger("tantra.orchestration.swarm")

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..agent import Agent
    from ..types import RunResult


# Swarm orchestration type constant
SWARM_TYPE = "swarm"


@dataclass
class Handoff:
    """Represents a handoff to another agent.

    Attributes:
        target: Name of the agent to hand off to.
        reason: Brief explanation for the handoff.
        context: Additional context data passed to the target agent.
    """

    target: str
    reason: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmStep(AgentStep):
    """Extended step with handoff information and trace.

    Attributes:
        handoff_to: Name of the agent this step handed off to, or None.
        handoff_reason: Reason for the handoff, or None.
        trace: Full log trace from the agent run.
    """

    handoff_to: str | None = None
    handoff_reason: str | None = None
    trace: list[LogEntry] = field(default_factory=list)


@dataclass
class SwarmDetail(OrchestrationDetail):
    """Detail payload for swarm orchestration results.

    Carried in ``RunResult.detail`` for swarm orchestration.
    Extends OrchestrationDetail with handoff-specific fields.

    Attributes:
        handoff_chain: Ordered list of agent names visited during execution.
    """

    handoff_chain: list[str] = field(default_factory=list)

    @property
    def handoff_count(self) -> int:
        """Number of handoffs that occurred."""
        return len(self.handoff_chain) - 1 if self.handoff_chain else 0


class Swarm(Orchestrator):
    """Swarm-style orchestration with dynamic agent handoffs.

    Agents can transfer control to each other during a conversation.
    Context (conversation history) is preserved across handoffs.

    Examples:
        ```python
        swarm = Swarm(
            agents={
                "triage": triage_agent,
                "billing": billing_agent,
                "support": support_agent,
            },
            handoffs={
                "triage": ["billing", "support"],
                "billing": ["triage"],
                "support": ["triage"],
            },
            entry_point="triage",
        )

        result = await swarm.run("I need a refund")
        print(result.handoff_chain)  # ["triage", "billing"]
        ```
    """

    def __init__(
        self,
        agents: dict[str, Agent],
        handoffs: dict[str, list[str]] | None = None,
        entry_point: str | None = None,
        max_handoffs: int = 10,
        preserve_memory: bool = True,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
        checkpoint_store: CheckpointStore | None = None,
        name: str | None = None,
    ):
        """Initialize swarm.

        Args:
            agents: Dict mapping names to agents.
            handoffs: Dict mapping agent names to list of agents they can hand off to.
                     If None, all agents can hand off to all other agents.
            entry_point: Name of the agent that handles initial requests.
                        Defaults to first agent in dict.
            max_handoffs: Maximum number of handoffs allowed (prevents infinite loops).
            preserve_memory: Whether to preserve conversation across handoffs.
            context_store: Optional store for persisting shared context across runs.
            hooks: Optional list of RunHooks for lifecycle notifications.
            checkpoint_store: Optional store for swarm checkpointing (crash recovery
                and interrupt/resume).
            name: Optional human-readable name for this orchestrator.

        Raises:
            ValueError: If entry_point or any handoff source/target is not in agents.
        """
        self._name = name
        self._context_store: ContextStore = context_store or MemoryContextStore()
        self._hooks: list[RunHooks] = hooks or []
        self._checkpoint_store: CheckpointStore | None = checkpoint_store
        self._agents = agents
        self._handoffs = handoffs or self._default_handoffs()
        self._entry_point = entry_point or next(iter(agents.keys()))
        self._max_handoffs = max_handoffs
        self._preserve_memory = preserve_memory

        # Validate
        if self._entry_point not in self._agents:
            raise ValueError(f"Entry point '{self._entry_point}' not in agents")

        for source, targets in self._handoffs.items():
            if source not in self._agents:
                raise ValueError(f"Handoff source '{source}' not in agents")
            for target in targets:
                if target not in self._agents:
                    raise ValueError(f"Handoff target '{target}' not in agents")

        # Create wrapped agents with handoff tools
        self._wrapped_agents: dict[str, Agent] = {}
        for name, agent in self._agents.items():
            self._wrapped_agents[name] = self._wrap_agent(name, agent)

    def _default_handoffs(self) -> dict[str, list[str]]:
        """Build default handoffs where each agent can hand off to all others.

        Returns:
            Dict mapping each agent name to a list of all other agent names.
        """
        return {name: [other for other in self._agents if other != name] for name in self._agents}

    def _wrap_agent(self, name: str, agent: Agent) -> Agent:
        """Wrap agent with handoff tools.

        Args:
            name: Name of the agent being wrapped.
            agent: Original agent instance.

        Returns:
            New Agent instance augmented with handoff, consult, and discovery tools.
        """
        targets = self._handoffs.get(name, [])

        if not targets:
            return agent

        # Create handoff, consult, and discovery tools
        handoff_tools = self._create_handoff_tools(name, targets)

        if agent.tools:
            combined_tools = ToolSet(list(agent.tools))
            for tool in handoff_tools:
                combined_tools.add(tool)
        else:
            combined_tools = ToolSet(handoff_tools)

        return agent.clone_with(
            tools=combined_tools,
            system_prompt=self._enhance_system_prompt(agent.system_prompt, targets),
            memory=agent.memory if self._preserve_memory else ConversationMemory(),
            name=name,
        )

    def _create_handoff_tools(self, name: str, targets: list[str]) -> list[ToolDefinition]:
        """Create handoff and consultation tool definitions.

        Args:
            name: Name of the agent that will own these tools.
            targets: List of agent names this agent can interact with.

        Returns:
            List of ToolDefinition instances for transfer, consult, and discovery.
        """
        tools = []

        # Transfer tools - hand off control completely
        for target in targets:
            handoff_fn = self._create_handoff_function(target)
            tool_def = ToolDefinition(
                func=handoff_fn,
                name=f"transfer_to_{target}",
                description=f"Transfer the conversation to the {target} agent. "
                f"Use this when the user's request should be handled by {target}. "
                f"You will NOT receive a response - control passes to {target}.",
            )
            tools.append(tool_def)

        # Consult tools - ask another agent and get response back
        for target in targets:
            consult_fn = self._create_consult_function(target)
            tool_def = ToolDefinition(
                func=consult_fn,
                name=f"consult_{target}",
                description=f"Ask the {target} agent a question and get their response. "
                f"Use this when you need input from {target} but want to "
                f"continue handling the conversation yourself.",
            )
            tools.append(tool_def)

        # List agents tool - discover available agents
        list_fn = self._create_list_agents_function(name)
        tools.append(
            ToolDefinition(
                func=list_fn,
                name="list_available_agents",
                description="List all available agents and their specializations. "
                "Use this to discover which agents you can transfer to or consult.",
            )
        )

        return tools

    def _create_handoff_function(self, target: str) -> Callable[..., Any]:
        """Create the transfer function for a target agent.

        Args:
            target: Name of the agent to transfer to.

        Returns:
            Async callable that produces a structured handoff dict.
        """

        async def handoff_fn(reason: str, summary: str = "") -> dict[str, Any]:
            """Transfer control to another agent.

            Args:
                reason: Brief reason for the handoff.
                summary: Summary of the conversation so far for context.
            """
            return {"__handoff__": True, "target": target, "reason": reason, "summary": summary}

        handoff_fn.__name__ = f"transfer_to_{target}"
        return handoff_fn

    def _create_consult_function(self, target: str) -> Callable[..., Any]:
        """Create the consult function for a target agent.

        Args:
            target: Name of the agent to consult.

        Returns:
            Async callable that queries the target agent and returns its response.
        """
        # Use original (unwrapped) agents: consulted agents answer directly
        # without attempting further handoffs.
        agents = self._agents

        async def consult_fn(question: str) -> str:
            """Ask another agent a question and get their response.

            Args:
                question: The question to ask the other agent.
            """
            # Actually run the consulted agent and return their response
            consulted_agent = agents[target]
            try:
                result = await consulted_agent.run(question)
                return f"[Response from {target}]: {result.output}"
            except Exception as e:
                return f"[Error consulting {target}]: {e}"

        consult_fn.__name__ = f"consult_{target}"
        return consult_fn

    def _create_list_agents_function(self, current_agent: str) -> Callable[..., Any]:
        """Create the list agents function.

        Args:
            current_agent: Name of the agent that will own this tool.

        Returns:
            Async callable that returns a formatted list of available agents.
        """
        agent_descriptions = {}
        for name, agent in self._agents.items():
            # Extract first line of system prompt as description
            prompt = agent.system_prompt or "No description"
            desc = prompt.split("\n")[0][:100]
            agent_descriptions[name] = desc

        async def list_agents_fn() -> str:
            """List all available agents."""
            lines = ["Available agents:"]
            for name, desc in agent_descriptions.items():
                marker = " (you)" if name == current_agent else ""
                targets = self._handoffs.get(name, [])
                can_reach = f" -> can reach: {', '.join(targets)}" if targets else ""
                lines.append(f"- {name}{marker}: {desc}{can_reach}")
            return "\n".join(lines)

        list_agents_fn.__name__ = "list_available_agents"
        return list_agents_fn

    def _enhance_system_prompt(self, original: str, targets: list[str]) -> str:
        """Add handoff instructions to system prompt.

        Args:
            original: The agent's original system prompt.
            targets: List of agent names available for handoff.

        Returns:
            Enhanced system prompt with handoff instructions appended.
        """
        handoff_list = ", ".join(targets)
        addition = (
            f"\n\nYou can interact with other agents: {handoff_list}."
            f"\n- transfer_to_<agent>: Hand off control completely (you won't get a response)"
            f"\n- consult_<agent>: Ask a question and get their response back"
            f"\n- list_available_agents: See all agents and their specializations"
            f"\nUse transfer for issues outside your expertise. Use consult when you need input but want to stay in control."
        )
        return original + addition

    @property
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        return SWARM_TYPE

    @property
    def agents(self) -> dict[str, Agent]:
        """Get dict of original agents."""
        return self._agents.copy()

    @property
    def entry_point(self) -> str:
        """Get entry point agent name."""
        return self._entry_point

    @property
    def handoffs(self) -> dict[str, list[str]]:
        """Get handoff configuration."""
        return {k: v.copy() for k, v in self._handoffs.items()}

    def clone(self, **kwargs: Any) -> Swarm:
        """Create a copy of this swarm with optional resource overrides.

        Args:
            **kwargs: Optional overrides. Recognised keys:
                ``context_store`` — session-scoped context store.
                ``checkpoint_store`` — checkpoint store for crash recovery / interrupts.

        Returns:
            A new Swarm sharing the same agents and handoff configuration.
        """
        return Swarm(
            agents=self._agents,
            handoffs=self._handoffs,
            entry_point=self._entry_point,
            max_handoffs=self._max_handoffs,
            preserve_memory=self._preserve_memory,
            context_store=kwargs.get("context_store", self._context_store),
            hooks=self._hooks,
            checkpoint_store=kwargs.get("checkpoint_store", self._checkpoint_store),
            name=self._name,
        )

    @trace_swarm_run
    async def run(
        self,
        user_input: str,
        run_id: UUID | None = None,
        shared_context: RunContext | None = None,
        session_id: str | None = None,
    ) -> RunResult[SwarmDetail]:
        """Run the swarm with the given input.

        Args:
            user_input: The user's input message.
            run_id: Optional parent run ID for trace correlation.
            shared_context: Optional RunContext shared across all agents in this run.
            session_id: Optional session ID for persisting shared context across runs.

        Returns:
            RunResult with SwarmDetail containing steps and handoff chain.
        """
        swarm_run_id = run_id or uuid4()  # Parent run ID for all agent runs
        ctx = await resolve_context(self._context_store, shared_context, session_id)

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_start",
                run_id=swarm_run_id,
                user_input=user_input,
                orchestration_type=self.orchestration_type,
                context=ctx,
            )

        logger = Logger(run_id=swarm_run_id)
        logger.start_run()

        # Log swarm start
        logger.log(
            LogType.PROMPT,
            data={
                "input": user_input,
                "entry_point": self._entry_point,
                "agents": list(self._agents.keys()),
            },
            metadata={"swarm_execution": True},
        )

        return await self._run_from(
            current_agent=self._entry_point,
            current_input=user_input,
            handoff_chain=[self._entry_point],
            handoff_count=0,
            steps=[],
            total_tokens=0,
            total_cost=0.0,
            ctx=ctx,
            swarm_run_id=swarm_run_id,
            session_id=session_id,
            logger=logger,
        )

    async def _run_from(
        self,
        *,
        current_agent: str,
        current_input: str,
        handoff_chain: list[str],
        handoff_count: int,
        steps: list[SwarmStep],
        total_tokens: int,
        total_cost: float,
        ctx: RunContext | None,
        swarm_run_id: UUID,
        session_id: str | None,
        logger: Logger,
    ) -> RunResult[SwarmDetail]:
        """Core handoff loop shared by ``run()`` and ``resume()``.

        Args:
            current_agent: Name of the agent to start executing.
            current_input: Input text for the current agent.
            handoff_chain: Mutable list of agent names visited so far.
            handoff_count: Number of handoffs completed so far.
            steps: Mutable list of completed SwarmSteps.
            total_tokens: Accumulated token count.
            total_cost: Accumulated estimated cost.
            ctx: Shared RunContext, or None.
            swarm_run_id: Run ID for tracing.
            session_id: Optional session ID for checkpointing.
            logger: Logger instance for this run.

        Returns:
            RunResult[SwarmDetail] with final output and execution details.
        """
        start_time = datetime.now(UTC)

        # Shared memory for context preservation
        shared_memory = ConversationMemory()
        sync_hwm = 0  # high-water mark for O(n) memory sync

        while True:
            # Clone to isolate memory across concurrent runs
            agent = self._wrapped_agents[current_agent].clone()

            # If preserving memory, sync with shared memory
            if self._preserve_memory and handoff_count > 0:
                for msg in shared_memory.get_messages():
                    agent.memory.add_message(msg)

            step_start = datetime.now(UTC)

            await self._emit_step(StreamEvent("agent_start", {
                "agent": current_agent,
            }))

            try:
                result = await agent.run(
                    current_input,
                    parent_run_id=swarm_run_id,
                    context=ctx,
                    on_event=self._active_on_event,
                )
                output = result.output

                handoff = self._detect_handoff(result)

                step = SwarmStep(
                    agent_id=current_agent,
                    input=current_input,
                    output=output,
                    metadata=result.metadata,
                    duration_ms=result.metadata.duration_ms,
                    handoff_to=handoff.target if handoff else None,
                    handoff_reason=handoff.reason if handoff else None,
                    trace=result.trace,
                )

                total_tokens += result.metadata.total_tokens
                total_cost += result.metadata.estimated_cost

                steps.append(step)

                await self._emit_step(StreamEvent("agent_complete", {
                    "agent": current_agent,
                    "output": output[:500],
                    "duration_ms": step.duration_ms,
                    "handoff_to": handoff.target if handoff else None,
                }))

                # Sync new messages to shared memory (O(n) via high-water mark)
                if self._preserve_memory:
                    agent_messages = agent.memory.get_messages()
                    for msg in agent_messages[sync_hwm:]:
                        shared_memory.add_message(msg)
                    sync_hwm = shared_memory.message_count

                if handoff:
                    handoff_count += 1

                    # Log handoff event
                    logger.log(
                        LogType.TOOL_RESULT,
                        data={
                            "event": "handoff",
                            "from_agent": step.agent_id,
                            "to_agent": handoff.target,
                            "reason": handoff.reason,
                            "summary": handoff.context.get("summary", ""),
                        },
                        metadata={"handoff_number": handoff_count},
                    )

                    if handoff_count > self._max_handoffs:
                        break

                    await self._emit_step(StreamEvent("handoff", {
                        "from_agent": step.agent_id,
                        "to_agent": handoff.target,
                        "reason": handoff.reason,
                    }))

                    # Hand off to next agent
                    current_agent = handoff.target
                    handoff_chain.append(current_agent)

                    # Prepare context for next agent
                    current_input = (
                        f"[Handoff from previous agent]\n"
                        f"Reason: {handoff.reason}\n"
                        f"Context: {handoff.context.get('summary', 'See conversation history')}\n\n"
                        f"Please continue helping the user."
                    )

                    # Save progress checkpoint after handoff
                    if self._checkpoint_store is not None:
                        await self._save_swarm_checkpoint(
                            swarm_run_id=swarm_run_id,
                            session_id=session_id,
                            checkpoint_type="swarm_progress",
                            current_agent=current_agent,
                            current_input=current_input,
                            handoff_chain=handoff_chain,
                            handoff_count=handoff_count,
                            steps=steps,
                            total_tokens=total_tokens,
                            total_cost=total_cost,
                            ctx=ctx,
                        )
                else:
                    # No handoff, we're done
                    break

            except ExecutionInterruptedError as e:
                # Save swarm-level interrupt checkpoint wrapping the agent's
                if self._checkpoint_store is not None:
                    swarm_cp_id = await self._save_swarm_checkpoint(
                        swarm_run_id=swarm_run_id,
                        session_id=session_id,
                        checkpoint_type="swarm_interrupt",
                        current_agent=current_agent,
                        current_input=current_input,
                        handoff_chain=handoff_chain,
                        handoff_count=handoff_count,
                        steps=steps,
                        total_tokens=total_tokens,
                        total_cost=total_cost,
                        ctx=ctx,
                        extra_context={
                            "agent_checkpoint_id": e.checkpoint_id,
                            "interrupted_agent": current_agent,
                        },
                    )
                    raise ExecutionInterruptedError(swarm_cp_id, e.prompt) from e
                raise

            except Exception as e:
                step = SwarmStep(
                    agent_id=current_agent,
                    input=current_input,
                    output="",
                    metadata=RunMetadata(
                        run_id=uuid4(),
                        total_tokens=0,
                        prompt_tokens=0,
                        completion_tokens=0,
                        estimated_cost=0,
                        duration_ms=0,
                        tool_calls_count=0,
                    ),
                    duration_ms=(datetime.now(UTC) - step_start).total_seconds() * 1000,
                    error=e,
                )
                steps.append(step)
                break

        total_duration = (datetime.now(UTC) - start_time).total_seconds() * 1000

        # Log swarm completion
        logger.log(
            LogType.FINAL_RESPONSE,
            data={
                "output": steps[-1].output[:500] if steps else "",
                "handoff_chain": handoff_chain,
                "total_handoffs": len(handoff_chain) - 1,
            },
            metadata={
                "duration_ms": total_duration,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
            },
        )

        await save_context(self._context_store, ctx, session_id)

        orch_result = RunResult(
            output=steps[-1].output if steps else "",
            trace=logger.entries,
            metadata=RunMetadata(
                run_id=swarm_run_id,
                total_tokens=total_tokens,
                prompt_tokens=sum(s.metadata.prompt_tokens for s in steps),
                completion_tokens=sum(s.metadata.completion_tokens for s in steps),
                estimated_cost=total_cost,
                duration_ms=total_duration,
                tool_calls_count=sum(s.metadata.tool_calls_count for s in steps),
            ),
            detail=SwarmDetail(
                steps=steps,
                orchestration_type=self.orchestration_type,
                handoff_chain=handoff_chain,
            ),
            context=ctx,
        )

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_end",
                run_id=swarm_run_id,
                result=orch_result,
                orchestration_type=self.orchestration_type,
                context=ctx,
            )

        return orch_result

    def _detect_handoff(self, result: RunResult) -> Handoff | None:
        """Detect if agent requested a handoff via structured tool result.

        Scans trace entries for tool results containing a handoff dict.
        Validates that the target agent exists before returning.

        Args:
            result: RunResult from the agent execution.

        Returns:
            Handoff instance if a valid handoff was requested, otherwise None.
        """
        for entry in result.trace:
            if entry.type.value == "tool_result":
                data = entry.data
                if not isinstance(data, dict):
                    continue
                result_str = data.get("result", "")
                if not isinstance(result_str, str):
                    continue
                try:
                    parsed = json.loads(result_str)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(parsed, dict) or not parsed.get("__handoff__"):
                    continue
                target = parsed.get("target", "")
                if target not in self._agents:
                    _logger.warning("Handoff target '%s' not found in agents, ignoring", target)
                    continue
                return Handoff(
                    target=target,
                    reason=parsed.get("reason", ""),
                    context={"summary": parsed.get("summary", "")},
                )
        return None

    async def _save_swarm_checkpoint(
        self,
        *,
        swarm_run_id: UUID,
        session_id: str | None,
        checkpoint_type: str,
        current_agent: str,
        current_input: str,
        handoff_chain: list[str],
        handoff_count: int,
        steps: list[SwarmStep],
        total_tokens: int,
        total_cost: float,
        ctx: RunContext | None,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Save a swarm checkpoint after a handoff or interrupt.

        Args:
            swarm_run_id: Run ID for this swarm execution.
            session_id: Optional session ID for grouping checkpoints.
            checkpoint_type: ``"swarm_progress"`` or ``"swarm_interrupt"``.
            current_agent: The agent to run next (progress) or the interrupted agent.
            current_input: Input text for the current/next agent.
            handoff_chain: Ordered list of agent names visited so far.
            handoff_count: Number of handoffs so far.
            steps: Completed SwarmSteps.
            total_tokens: Accumulated token count.
            total_cost: Accumulated estimated cost.
            ctx: Shared RunContext, or None.
            extra_context: Additional fields merged into the checkpoint context.

        Returns:
            The saved checkpoint ID.
        """
        context_data: dict[str, Any] = {
            "current_agent": current_agent,
            "current_input": current_input,
            "handoff_chain": list(handoff_chain),
            "handoff_count": handoff_count,
            "steps": [_serialize_step(s) for s in steps],
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "context_data": ctx.to_dict() if ctx else None,
            "swarm_name": self._name,
        }
        if extra_context:
            context_data.update(extra_context)

        checkpoint = Checkpoint(
            name=self._name or "swarm",
            run_id=swarm_run_id,
            session_id=session_id,
            checkpoint_type=checkpoint_type,
            messages=[],
            context=context_data,
            status="pending",
        )
        return await self._checkpoint_store.save(checkpoint)

    async def resume(
        self,
        checkpoint_id: str,
        checkpoint_store: CheckpointStore | None = None,
        response: InterruptResponse | None = None,
    ) -> RunResult[SwarmDetail]:
        """Resume swarm execution from a checkpoint.

        Supports two checkpoint types:

        - ``"swarm_progress"`` — crash recovery. Resumes from the next
          agent in the handoff chain. No ``response`` needed.
        - ``"swarm_interrupt"`` — an agent's tool triggered a
          human-in-the-loop interrupt. Supply a ``response`` to answer
          the interrupt, resume the agent, then continue the swarm.

        Args:
            checkpoint_id: ID of the checkpoint to resume from.
            checkpoint_store: Optional store override; falls back to
                ``self._checkpoint_store``.
            response: Required for ``"swarm_interrupt"`` checkpoints.
                The human's response to the interrupted tool.

        Returns:
            RunResult[SwarmDetail] with final output and execution details.

        Raises:
            ConfigurationError: If no checkpoint store is available.
            ValueError: If the checkpoint is not found, has wrong type,
                or ``response`` is missing for an interrupt checkpoint.
        """
        store = checkpoint_store or self._checkpoint_store
        if store is None:
            raise ConfigurationError(
                "No checkpoint store available. Pass checkpoint_store to Swarm() or resume()."
            )

        checkpoint = await store.load(checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        if checkpoint.checkpoint_type == "swarm_interrupt":
            return await self._resume_interrupt(checkpoint, store, response)
        elif checkpoint.checkpoint_type == "swarm_progress":
            return await self._resume_progress(checkpoint, store)
        else:
            raise ValueError(
                f"Expected checkpoint_type 'swarm_progress' or 'swarm_interrupt', "
                f"got '{checkpoint.checkpoint_type}'"
            )

    async def _resume_progress(
        self,
        checkpoint: Checkpoint,
        store: CheckpointStore,
    ) -> RunResult[SwarmDetail]:
        """Resume from a ``swarm_progress`` checkpoint (crash recovery).

        Restores accumulated state and re-enters the handoff loop from
        the agent that was about to run when the checkpoint was saved.

        Args:
            checkpoint: The loaded checkpoint.
            store: The checkpoint store used for loading.

        Returns:
            RunResult[SwarmDetail] from the continued execution.
        """
        ctx_data = checkpoint.context
        await store.update(checkpoint.id, status="completed")

        # Restore state
        current_agent = ctx_data["current_agent"]
        current_input = ctx_data["current_input"]
        handoff_chain = list(ctx_data["handoff_chain"])
        handoff_count = ctx_data["handoff_count"]
        steps = [_deserialize_step(s) for s in ctx_data["steps"]]
        total_tokens = ctx_data["total_tokens"]
        total_cost = ctx_data["total_cost"]
        context_data = ctx_data.get("context_data")
        ctx = RunContext(context_data) if context_data else None

        swarm_run_id = checkpoint.run_id
        logger = Logger(run_id=swarm_run_id)
        logger.start_run()

        logger.log(
            LogType.PROMPT,
            data={
                "swarm_name": self._name,
                "resumed_from": checkpoint.id,
                "current_agent": current_agent,
                "handoff_chain": handoff_chain,
            },
            metadata={"swarm_resume": True},
        )

        return await self._run_from(
            current_agent=current_agent,
            current_input=current_input,
            handoff_chain=handoff_chain,
            handoff_count=handoff_count,
            steps=steps,
            total_tokens=total_tokens,
            total_cost=total_cost,
            ctx=ctx,
            swarm_run_id=swarm_run_id,
            session_id=checkpoint.session_id,
            logger=logger,
        )

    async def _resume_interrupt(
        self,
        checkpoint: Checkpoint,
        store: CheckpointStore,
        response: InterruptResponse | None,
    ) -> RunResult[SwarmDetail]:
        """Resume from a ``swarm_interrupt`` checkpoint (human-in-the-loop).

        Resumes the interrupted agent, records its output, then continues
        the handoff loop if the agent triggers another handoff.

        Args:
            checkpoint: The loaded checkpoint.
            store: The checkpoint store used for loading.
            response: The human's response. Required.

        Returns:
            RunResult[SwarmDetail] from the continued execution.

        Raises:
            ValueError: If *response* is None or the interrupted agent
                cannot be found.
        """
        if response is None:
            raise ValueError("InterruptResponse required to resume a 'swarm_interrupt' checkpoint.")

        ctx_data = checkpoint.context
        await store.update(checkpoint.id, status="completed")

        agent_checkpoint_id = ctx_data["agent_checkpoint_id"]
        interrupted_agent = ctx_data["interrupted_agent"]
        current_input = ctx_data["current_input"]
        handoff_chain = list(ctx_data["handoff_chain"])
        handoff_count = ctx_data["handoff_count"]
        steps = [_deserialize_step(s) for s in ctx_data["steps"]]
        total_tokens = ctx_data["total_tokens"]
        total_cost = ctx_data["total_cost"]
        context_data = ctx_data.get("context_data")
        ctx = RunContext(context_data) if context_data else None

        swarm_run_id = checkpoint.run_id

        # Resume the interrupted agent
        agent = self._wrapped_agents[interrupted_agent].clone()
        agent_result = await agent.resume(agent_checkpoint_id, response)

        # Detect handoff from resumed agent
        handoff = self._detect_handoff(agent_result)

        step = SwarmStep(
            agent_id=interrupted_agent,
            input=current_input,
            output=agent_result.output,
            metadata=agent_result.metadata,
            duration_ms=agent_result.metadata.duration_ms,
            handoff_to=handoff.target if handoff else None,
            handoff_reason=handoff.reason if handoff else None,
            trace=agent_result.trace,
        )
        steps.append(step)
        total_tokens += agent_result.metadata.total_tokens
        total_cost += agent_result.metadata.estimated_cost

        logger = Logger(run_id=swarm_run_id)
        logger.start_run()

        logger.log(
            LogType.PROMPT,
            data={
                "swarm_name": self._name,
                "resumed_from": checkpoint.id,
                "interrupted_agent": interrupted_agent,
                "agent_checkpoint_id": agent_checkpoint_id,
            },
            metadata={"swarm_interrupt_resume": True},
        )

        if handoff:
            handoff_count += 1
            if handoff_count <= self._max_handoffs:
                next_agent = handoff.target
                handoff_chain.append(next_agent)
                next_input = (
                    f"[Handoff from previous agent]\n"
                    f"Reason: {handoff.reason}\n"
                    f"Context: {handoff.context.get('summary', 'See conversation history')}\n\n"
                    f"Please continue helping the user."
                )
                return await self._run_from(
                    current_agent=next_agent,
                    current_input=next_input,
                    handoff_chain=handoff_chain,
                    handoff_count=handoff_count,
                    steps=steps,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    ctx=ctx,
                    swarm_run_id=swarm_run_id,
                    session_id=checkpoint.session_id,
                    logger=logger,
                )

        # No handoff or max handoffs exceeded — build final result
        await save_context(self._context_store, ctx, checkpoint.session_id)

        orch_result = RunResult(
            output=steps[-1].output if steps else "",
            trace=logger.entries,
            metadata=RunMetadata(
                run_id=swarm_run_id,
                total_tokens=total_tokens,
                prompt_tokens=sum(s.metadata.prompt_tokens for s in steps),
                completion_tokens=sum(s.metadata.completion_tokens for s in steps),
                estimated_cost=total_cost,
                duration_ms=0,
                tool_calls_count=sum(s.metadata.tool_calls_count for s in steps),
            ),
            detail=SwarmDetail(
                steps=steps,
                orchestration_type=self.orchestration_type,
                handoff_chain=handoff_chain,
            ),
            context=ctx,
        )

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_end",
                run_id=swarm_run_id,
                result=orch_result,
                orchestration_type=self.orchestration_type,
                context=ctx,
            )

        return orch_result


def _serialize_step(step: SwarmStep) -> dict[str, Any]:
    """Serialize a SwarmStep to a JSON-safe dict for checkpoint storage."""
    return {
        "agent_id": step.agent_id,
        "input": step.input,
        "output": step.output,
        "metadata": step.metadata.model_dump(mode="json"),
        "duration_ms": step.duration_ms,
        "handoff_to": step.handoff_to,
        "handoff_reason": step.handoff_reason,
        "error": str(step.error) if step.error else None,
    }


def _deserialize_step(data: dict[str, Any]) -> SwarmStep:
    """Deserialize a dict back into a SwarmStep."""
    return SwarmStep(
        agent_id=data["agent_id"],
        input=data["input"],
        output=data["output"],
        metadata=RunMetadata(**data["metadata"]),
        duration_ms=data.get("duration_ms") or 0,
        handoff_to=data.get("handoff_to"),
        handoff_reason=data.get("handoff_reason"),
        error=RuntimeError(data["error"]) if data.get("error") else None,
    )


def swarm(
    agents: dict[str, Agent],
    handoffs: dict[str, list[str]] | None = None,
    entry_point: str | None = None,
    max_handoffs: int = 10,
    preserve_memory: bool = True,
    context_store: ContextStore | None = None,
    hooks: list[RunHooks] | None = None,
    checkpoint_store: CheckpointStore | None = None,
    name: str | None = None,
) -> Swarm:
    """Create a swarm orchestrator.

    Convenience function for quick swarm creation.

    Args:
        agents: Dict mapping names to agents.
        handoffs: Optional handoff configuration. Defaults to all-to-all.
        entry_point: Name of the initial agent. Defaults to first agent.
        max_handoffs: Maximum number of handoffs allowed. Default 10.
        preserve_memory: Whether to preserve conversation across handoffs. Default True.
        context_store: Optional store for persisting shared context.
        hooks: Optional list of RunHooks for lifecycle notifications.
        checkpoint_store: Optional store for swarm checkpointing.
        name: Optional human-readable name for this orchestrator.

    Returns:
        Configured Swarm instance.

    Examples:
        ```python
        s = swarm(
            {"triage": agent1, "billing": agent2},
            handoffs={"triage": ["billing"], "billing": ["triage"]},
            entry_point="triage",
        )
        result = await s.run("Help with billing")
        ```
    """
    return Swarm(
        agents=agents,
        handoffs=handoffs,
        entry_point=entry_point,
        max_handoffs=max_handoffs,
        preserve_memory=preserve_memory,
        context_store=context_store,
        hooks=hooks,
        checkpoint_store=checkpoint_store,
        name=name,
    )
