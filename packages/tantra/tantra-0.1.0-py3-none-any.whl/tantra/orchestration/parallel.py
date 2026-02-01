"""Parallel orchestration pattern.

Run multiple agents concurrently and combine their results.
Useful for gathering multiple perspectives or parallel processing.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ..context import ContextStore, MemoryContextStore, RunContext
from ..exceptions import ContextMergeConflictError
from ..hooks import RunHooks, _invoke_hooks
from ..observability import trace_orchestration_run
from ..types import RunMetadata, RunResult, StreamEvent
from .base import AgentStep, OrchestrationDetail, Orchestrator, resolve_context, save_context

if TYPE_CHECKING:
    from ..agent import Agent


class Parallel(Orchestrator):
    """Run multiple agents in parallel.

    All agents receive the same input and run concurrently.
    Results are combined using a configurable strategy.

    Examples:
        ```python
        parallel = Parallel(
            agents=[
                ("analyst_1", analyst_agent_1),
                ("analyst_2", analyst_agent_2),
                ("analyst_3", analyst_agent_3),
            ],
            combine_fn=lambda results: "\\n---\\n".join(r.output for r in results),
        )

        result = await parallel.run("Analyze this market data")
        # All analysts run concurrently, outputs combined
        ```
    """

    def __init__(
        self,
        agents: list[tuple[str, Agent] | Agent],
        combine_fn: Callable[[list[AgentStep]], str] | None = None,
        fail_fast: bool = False,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
        name: str | None = None,
    ):
        """Initialize parallel orchestrator.

        Args:
            agents: List of agents or (name, agent) tuples.
            combine_fn: Function to combine results. Default joins with newlines.
            fail_fast: If True, cancel remaining agents on first error.
            context_store: Optional store for persisting shared context across runs.
            hooks: Optional list of RunHooks for lifecycle notifications.
            name: Optional human-readable name for this orchestrator.
        """
        self._name = name
        self._context_store: ContextStore = context_store or MemoryContextStore()
        self._hooks: list[RunHooks] = hooks or []
        self._agents: list[tuple[str, Agent]] = []
        for item in agents:
            if isinstance(item, tuple):
                self._agents.append(item)
            else:
                name = getattr(item, "name", None) or f"agent_{len(self._agents)}"
                self._agents.append((name, item))

        self.combine_fn = combine_fn or self._default_combine
        self.fail_fast = fail_fast

    @staticmethod
    def _default_combine(steps: list[AgentStep]) -> str:
        """Default combination: join outputs with separators."""
        parts = []
        for step in steps:
            if step.output:
                parts.append(f"[{step.agent_id}]\n{step.output}")
        return "\n\n".join(parts)

    @property
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        return "parallel"

    @property
    def agents(self) -> list[tuple[str, Agent]]:
        """Get list of (name, agent) tuples."""
        return self._agents.copy()

    def clone(self, **kwargs: Any) -> Parallel:
        """Create a copy of this parallel orchestrator with optional resource overrides.

        Args:
            **kwargs: Optional overrides. Recognised keys:
                ``context_store`` — session-scoped context store.

        Returns:
            A new Parallel sharing the same agents and combine function.
        """
        return Parallel(
            agents=self._agents,
            combine_fn=self.combine_fn,
            fail_fast=self.fail_fast,
            context_store=kwargs.get("context_store", self._context_store),
            hooks=self._hooks,
            name=self._name,
        )

    async def _run_agent(
        self,
        name: str,
        agent: Agent,
        user_input: str,
        parent_run_id: UUID | None = None,
        context: RunContext | None = None,
    ) -> tuple[AgentStep, RunContext | None]:
        """Run a single agent and return its step and context.

        Args:
            name: Identifier for the agent.
            agent: The agent to execute.
            user_input: Input text for the agent.
            parent_run_id: Optional parent run ID for trace correlation.
            context: Optional RunContext copy for this agent.
        """
        step_start = datetime.now(UTC)

        try:
            result = await agent.run(user_input, parent_run_id=parent_run_id, context=context)
            step = AgentStep(
                agent_id=name,
                input=user_input,
                output=result.output,
                metadata=result.metadata,
                duration_ms=result.metadata.duration_ms,
            )
            await self._emit_step(StreamEvent("agent_complete", {
                "agent": name, "output": result.output[:500],
                "duration_ms": step.duration_ms,
            }))
            return step, context
        except Exception as e:
            step = AgentStep(
                agent_id=name,
                input=user_input,
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
            await self._emit_step(StreamEvent("agent_complete", {
                "agent": name, "error": str(e),
                "duration_ms": step.duration_ms,
            }))
            return step, context

    @staticmethod
    def _merge_contexts(
        original_snapshot: dict[str, Any],
        agent_copies: list[tuple[str, RunContext]],
        target: RunContext,
    ) -> None:
        """Merge per-agent context copies back into the target context.

        For each copy, compute the diff vs. the original snapshot (keys that
        were added or changed). Then merge all diffs into *target*.

        Args:
            original_snapshot: Snapshot of the context before parallel execution.
            agent_copies: List of (name, RunContext) copies to merge.
            target: The original RunContext to merge results into.

        Raises:
            ContextMergeConflictError: If two agents wrote different values to the
                same key.
        """
        # Collect diffs: key -> list of (name, value)
        diffs: dict[str, list[tuple[str, Any]]] = {}
        for name, copy in agent_copies:
            for key, value in copy.to_dict().items():
                original_value = original_snapshot.get(key, _SENTINEL)
                if value is not original_value and value != original_value:
                    diffs.setdefault(key, []).append((name, value))

        # Apply diffs, detecting conflicts
        for key, writes in diffs.items():
            # Deduplicate — if multiple agents wrote the same value, no conflict
            distinct: list[tuple[str, Any]] = []
            seen_values: list[Any] = []
            for name, v in writes:
                is_dup = False
                for sv in seen_values:
                    if v is sv or v == sv:
                        is_dup = True
                        break
                if not is_dup:
                    distinct.append((name, v))
                    seen_values.append(v)

            if len(distinct) > 1:
                raise ContextMergeConflictError(
                    key=key,
                    agents=[name for name, _ in writes],
                    values=[v for _, v in writes],
                )

            # Safe — all agents agree (or only one wrote)
            target.set(key, writes[0][1])

    @trace_orchestration_run("parallel")
    async def run(
        self,
        user_input: str,
        run_id: UUID | None = None,
        shared_context: RunContext | None = None,
        session_id: str | None = None,
    ) -> RunResult[OrchestrationDetail]:
        """Run all agents in parallel.

        Each agent receives a **copy** of the shared context. After all agents
        complete, per-agent writes are merged back into the original context.

        Args:
            user_input: Input text sent to every agent.
            run_id: Optional run ID for trace correlation.
            shared_context: Optional RunContext shared across agents (each agent
                receives a copy; writes are merged afterward).
            session_id: Optional session ID for persisting shared context.

        Returns:
            RunResult with OrchestrationDetail containing step details.

        Raises:
            ContextMergeConflictError: If two agents wrote different values to the
                same key.
        """
        orchestration_id = run_id or uuid4()
        ctx = await resolve_context(self._context_store, shared_context, session_id)

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_start",
                run_id=orchestration_id,
                user_input=user_input,
                orchestration_type=self.orchestration_type,
                context=ctx,
            )

        start_time = datetime.now(UTC)

        await self._emit_step(StreamEvent("fan_out", {
            "agents": [name for name, _ in self._agents],
        }))

        # Snapshot the original context and create per-agent copies
        if ctx is not None:
            original_snapshot = ctx.to_dict()
            agent_copies = [(name, ctx.copy()) for name, _ in self._agents]
        else:
            original_snapshot = {}
            agent_copies = [(name, None) for name, _ in self._agents]

        # Create actual Task objects (not just coroutines) for proper cancellation
        tasks = [
            asyncio.create_task(
                self._run_agent(
                    name,
                    agent,
                    user_input,
                    parent_run_id=orchestration_id,
                    context=agent_copies[i][1],
                )
            )
            for i, (name, agent) in enumerate(self._agents)
        ]

        # Run concurrently
        if self.fail_fast:
            # Use gather with return_exceptions=False to fail on first error
            try:
                results = await asyncio.gather(*tasks)
            except Exception:
                # Cancel remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()
                raise
            steps = [r[0] for r in results]
        else:
            # Collect all results, including errors
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)
            # Wrap any bare exceptions (e.g. CancelledError) that bypassed _run_agent's handler
            steps = []
            for i, r in enumerate(raw_results):
                if isinstance(r, tuple):
                    steps.append(r[0])
                else:
                    # Raw exception leaked — wrap it so callers see the failure in steps
                    name = self._agents[i][0] if i < len(self._agents) else f"agent_{i}"
                    steps.append(
                        AgentStep(
                            agent_id=name,
                            input=user_input,
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
                            duration_ms=0,
                            error=r if isinstance(r, Exception) else RuntimeError(str(r)),
                        )
                    )

        # Merge per-agent context copies back into the original
        if ctx is not None:
            copies_with_data = [(name, copy) for (name, copy) in agent_copies if copy is not None]
            self._merge_contexts(original_snapshot, copies_with_data, ctx)

        # Combine results
        output = self.combine_fn(steps)

        await self._emit_step(StreamEvent("fan_in", {
            "output": output[:500],
        }))

        total_duration = (datetime.now(UTC) - start_time).total_seconds() * 1000

        await save_context(self._context_store, ctx, session_id)

        orch_result = RunResult(
            output=output,
            trace=[],
            metadata=RunMetadata(
                run_id=orchestration_id,
                total_tokens=sum(s.metadata.total_tokens for s in steps),
                prompt_tokens=sum(s.metadata.prompt_tokens for s in steps),
                completion_tokens=sum(s.metadata.completion_tokens for s in steps),
                estimated_cost=sum(s.metadata.estimated_cost for s in steps),
                duration_ms=total_duration,
                tool_calls_count=sum(s.metadata.tool_calls_count for s in steps),
            ),
            detail=OrchestrationDetail(
                steps=list(steps),
                orchestration_type=self.orchestration_type,
            ),
            context=ctx,
        )

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_end",
                run_id=orchestration_id,
                result=orch_result,
                orchestration_type=self.orchestration_type,
                context=ctx,
            )

        return orch_result


_SENTINEL = object()


def fan_out(*agents: Agent) -> Parallel:
    """Create a parallel orchestrator from agents.

    Convenience function for quick parallel creation.

    Args:
        *agents: Agents to execute in parallel.

    Returns:
        Parallel orchestrator configured with the given agents.

    Examples:
        ```python
        result = await fan_out(agent1, agent2, agent3).run("input")
        ```
    """
    return Parallel(list(agents))
