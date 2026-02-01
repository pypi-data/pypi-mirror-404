"""Base classes and types for multi-agent orchestration.

This module provides the foundation for orchestration patterns:
- AgentStep: Result of a single agent execution
- OrchestrationDetail: Detail payload for orchestration results
- Orchestrator: Abstract base class for all servable units
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from ..context import ContextStore, RunContext
from ..types import RunMetadata, RunResult, StreamEvent


async def resolve_context(
    context_store: ContextStore,
    shared_context: RunContext | None,
    session_id: str | None,
) -> RunContext | None:
    """Resolve the RunContext for an orchestration run.

    Priority: explicit shared_context > session_id load > None.
    Returns None when neither is provided (each agent uses its own context).

    Args:
        context_store: Store used to load persisted context.
        shared_context: Explicit RunContext to use if provided.
        session_id: Session ID for loading persisted context from the store.

    Returns:
        Resolved RunContext, or None when neither shared_context nor session_id
        is provided.
    """
    if shared_context is not None:
        return shared_context
    if session_id:
        saved = await context_store.load(session_id)
        return RunContext(saved) if saved else RunContext()
    return None


async def save_context(
    context_store: ContextStore,
    context: RunContext | None,
    session_id: str | None,
) -> None:
    """Save context to the store if session_id is provided.

    Args:
        context_store: Store used to persist context.
        context: RunContext to save, or None (no-op).
        session_id: Session ID under which to persist. None means skip.
    """
    if context is not None and session_id:
        await context_store.save(session_id, context.to_dict())


@dataclass
class AgentStep:
    """Result of a single agent step in orchestration.

    Attributes:
        agent_id: Identifier of the agent that executed this step.
        input: Input text provided to the agent.
        output: Output text produced by the agent.
        metadata: Run metadata including token counts and cost.
        duration_ms: Wall-clock duration of the step in milliseconds.
        error: Exception raised during execution, or None on success.
    """

    agent_id: str
    input: str
    output: str
    metadata: RunMetadata
    duration_ms: float
    error: Exception | None = None


@dataclass
class OrchestrationDetail:
    """Detail payload for orchestration results.

    Carried in ``RunResult.detail`` for Pipeline, Router, and Parallel
    orchestration patterns.

    Attributes:
        steps: Individual agent steps executed during orchestration.
        orchestration_type: Name of the orchestration pattern used.
    """

    steps: list[AgentStep]
    orchestration_type: str

    @property
    def success(self) -> bool:
        """Whether all steps completed successfully."""
        return all(step.error is None for step in self.steps)

    @property
    def agent_count(self) -> int:
        """Number of distinct agents that participated."""
        return len(set(step.agent_id for step in self.steps))


class Orchestrator(ABC):
    """Abstract base for all servable units in Tantra.

    Extensible: SDK users subclass this to create custom orchestration
    patterns. Concrete implementations: Solo, Graph, Swarm, Pipeline,
    Parallel, Router.

    Streaming is built in via :meth:`stream`, which uses an
    ``asyncio.Queue`` to yield :class:`StreamEvent` objects pushed by
    :meth:`_emit_step` during execution. Subclasses add ``_emit_step()``
    calls in their execution loops — no need to override ``stream()``.
    """

    _name: str | None = None
    _step_queue: asyncio.Queue | None = None

    @property
    def name(self) -> str | None:
        """Human-readable name for this orchestrator."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        self._name = value

    @abstractmethod
    async def run(self, user_input: str, **kwargs: Any) -> RunResult:
        """Run the orchestration with the given input.

        Args:
            user_input: The input to process.
            **kwargs: Pattern-specific arguments (e.g. ``run_id``,
                ``shared_context``, ``session_id``).

        Returns:
            RunResult with output and pattern-specific detail.
        """
        pass

    async def stream(self, user_input: str, **kwargs: Any) -> AsyncIterator[StreamEvent]:
        """Stream execution events via asyncio.Queue.

        Default implementation: runs ``self.run()`` in a background task,
        yields ``StreamEvent`` objects pushed by ``_emit_step()``, then
        yields the final ``"complete"`` event.

        Subclasses add ``_emit_step()`` calls in their execution loops —
        no need to override ``stream()``.

        Args:
            user_input: The input to process.
            **kwargs: Pattern-specific arguments.

        Yields:
            StreamEvent objects as execution progresses.
        """
        self._step_queue = asyncio.Queue()

        async def _execute():
            try:
                return await self.run(user_input, **kwargs)
            except Exception as exc:
                await self._step_queue.put(exc)
                raise
            finally:
                await self._step_queue.put(None)  # sentinel

        task = asyncio.create_task(_execute())

        while True:
            item = await self._step_queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                self._step_queue = None
                raise item
            yield item

        self._step_queue = None
        result = task.result()
        yield StreamEvent(
            "complete",
            {
                "output": result.output,
                "metadata": result.metadata,
                "detail": result.detail,
            },
        )

    async def resume(
        self, checkpoint_id: str, response: Any = None, **kwargs: Any
    ) -> RunResult:
        """Resume from a checkpoint after human input.

        Not supported by default — subclasses that support
        checkpointing should override this method.

        Raises:
            NotImplementedError: Always, unless overridden.
        """
        raise NotImplementedError("resume() is not supported for this orchestrator")

    def clone(self, **kwargs: Any) -> Orchestrator:
        """Create a copy with fresh state for session isolation.

        Not supported by default — subclasses that support
        cloning should override this method.

        Raises:
            NotImplementedError: Always, unless overridden.
        """
        raise NotImplementedError("clone() is not supported for this orchestrator")

    @property
    @abstractmethod
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        pass

    @property
    def _active_on_event(self) -> Any:
        """Return the event callback when streaming, None otherwise.

        Use this when passing ``on_event`` to ``agent.run()`` so that the
        engine only switches to the streaming provider API when the
        orchestrator is actually streaming.
        """
        return self._emit_step if self._step_queue is not None else None

    async def _emit_step(self, event: StreamEvent) -> None:
        """Push an event to the stream queue (no-op when not streaming)."""
        if self._step_queue is not None:
            await self._step_queue.put(event)
