"""Pipeline orchestration pattern.

Sequential execution of agents where each agent's output becomes
the next agent's input. Useful for multi-stage processing.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ..context import ContextStore, MemoryContextStore, RunContext
from ..hooks import RunHooks, _invoke_hooks
from ..observability import trace_orchestration_run
from ..types import RunMetadata, RunResult, StreamEvent
from .base import AgentStep, OrchestrationDetail, Orchestrator, resolve_context, save_context

if TYPE_CHECKING:
    from ..agent import Agent


class Pipeline(Orchestrator):
    """Sequential execution of agents.

    Each agent's output becomes the next agent's input.
    Useful for multi-stage processing like: research -> write -> edit.

    Examples:
        ```python
        pipeline = Pipeline([
            ("researcher", research_agent),
            ("writer", writer_agent),
            ("editor", editor_agent),
        ])

        result = await pipeline.run("Write about quantum computing")
        # researcher runs first, output goes to writer, then to editor
        ```
    """

    def __init__(
        self,
        agents: list[tuple[str, Agent] | Agent],
        transform_fn: Callable[[str, str], str] | None = None,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
        name: str | None = None,
    ):
        """Initialize pipeline.

        Args:
            agents: List of agents or (name, agent) tuples.
            transform_fn: Optional function to transform output before next agent.
                         Takes (name, output) and returns transformed input.
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
                # Use agent name or generate one
                name = getattr(item, "name", None) or f"agent_{len(self._agents)}"
                self._agents.append((name, item))

        self.transform_fn = transform_fn

    @property
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        return "pipeline"

    @property
    def agents(self) -> list[tuple[str, Agent]]:
        """Get list of (name, agent) tuples."""
        return self._agents.copy()

    def clone(self, **kwargs: Any) -> Pipeline:
        """Create a copy of this pipeline with optional resource overrides.

        Args:
            **kwargs: Optional overrides. Recognised keys:
                ``context_store`` — session-scoped context store.

        Returns:
            A new Pipeline sharing the same agents and transform function.
        """
        return Pipeline(
            agents=self._agents,
            transform_fn=self.transform_fn,
            context_store=kwargs.get("context_store", self._context_store),
            hooks=self._hooks,
            name=self._name,
        )

    @trace_orchestration_run("pipeline")
    async def run(
        self,
        user_input: str,
        run_id: UUID | None = None,
        shared_context: RunContext | None = None,
        session_id: str | None = None,
    ) -> RunResult[OrchestrationDetail]:
        """Run agents in sequence, piping each output to the next.

        Args:
            user_input: Initial input to the first agent in the pipeline.
            run_id: Optional run ID for trace correlation.
            shared_context: Optional RunContext shared across all agents.
            session_id: Optional session ID for persisting shared context.

        Returns:
            RunResult with OrchestrationDetail containing step details.

        Raises:
            Exception: Propagated from agent execution; the pipeline stops on
                the first error and records it in the corresponding step.
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

        steps: list[AgentStep] = []
        current_input = user_input
        total_tokens = 0
        total_cost = 0.0

        start_time = datetime.now(UTC)

        for idx, (name, agent) in enumerate(self._agents):
            step_start = datetime.now(UTC)

            await self._emit_step(StreamEvent("stage_start", {
                "agent": name, "index": idx, "total": len(self._agents),
            }))

            try:
                result = await agent.run(
                    current_input,
                    parent_run_id=orchestration_id,
                    context=ctx,
                    on_event=self._active_on_event,
                )
                output = result.output

                step = AgentStep(
                    agent_id=name,
                    input=current_input,
                    output=output,
                    metadata=result.metadata,
                    duration_ms=result.metadata.duration_ms,
                )

                total_tokens += result.metadata.total_tokens
                total_cost += result.metadata.estimated_cost

                # Transform output for next agent if configured
                if self.transform_fn:
                    current_input = self.transform_fn(name, output)
                else:
                    current_input = output

            except Exception as e:
                step = AgentStep(
                    agent_id=name,
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
                break  # Stop pipeline on error

            steps.append(step)

            await self._emit_step(StreamEvent("stage_complete", {
                "agent": name, "output": output[:500],
                "duration_ms": step.duration_ms, "index": idx,
            }))

        total_duration = (datetime.now(UTC) - start_time).total_seconds() * 1000

        await save_context(self._context_store, ctx, session_id)

        orch_result = RunResult(
            output=steps[-1].output if steps else "",
            trace=[],
            metadata=RunMetadata(
                run_id=orchestration_id,
                total_tokens=total_tokens,
                prompt_tokens=sum(s.metadata.prompt_tokens for s in steps),
                completion_tokens=sum(s.metadata.completion_tokens for s in steps),
                estimated_cost=total_cost,
                duration_ms=total_duration,
                tool_calls_count=sum(s.metadata.tool_calls_count for s in steps),
            ),
            detail=OrchestrationDetail(
                steps=steps,
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


def chain(*agents: Agent) -> Pipeline:
    """Create a simple pipeline from agents.

    Convenience function for quick pipeline creation.

    Args:
        *agents: Agents to execute in sequence.

    Returns:
        Pipeline configured with the given agents.

    Examples:
        ```python
        result = await chain(agent1, agent2, agent3).run("input")
        ```
    """
    return Pipeline(list(agents))
