"""Lifecycle hooks for Tantra agent runs and orchestrations.

Hooks provide a mechanism to run custom code at key points during
agent execution (before/after runs, around tool calls) and orchestration
execution (before/after pipelines, graphs, swarms, etc.).

Hooks receive the RunContext and can inject data into it for tools
to consume (e.g., DB connections, session state). Hook errors are
logged but never crash the agent run or orchestration.

Example::

    from tantra import Agent, RunHooks

    class MetricsHook(RunHooks):
        async def on_run_start(self, *, run_id, user_input, name, context):
            print(f"Run {run_id} started for agent {name}")

        async def on_run_end(self, *, run_id, result, context):
            print(f"Run {run_id} completed in {result.metadata.duration_ms}ms")

    agent = Agent("openai:gpt-4o", hooks=[MetricsHook()])
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from .context import RunContext
    from .types import RunResult

logger = logging.getLogger("tantra.hooks")


class RunHooks:
    """Base class for agent lifecycle hooks.

    Override any subset of methods to receive notifications at key
    execution points. All methods are no-ops by default.

    Hook methods are always async. Errors in hooks are logged but
    never propagate to the caller.
    """

    async def on_run_start(
        self,
        *,
        run_id: UUID,
        user_input: str,
        name: str | None = None,
        context: RunContext,
    ) -> None:
        """Called when an agent run begins (after rules check, before engine).

        Args:
            run_id: Unique identifier for this run.
            user_input: The user's input message.
            name: The agent's name, if set.
            context: The RunContext for this run. Hooks can read/write
                     to share data with tools.
        """

    async def on_run_end(
        self,
        *,
        run_id: UUID,
        result: RunResult,
        context: RunContext,
    ) -> None:
        """Called when an agent run completes successfully.

        Only fired by ``agent.run()``, not streaming methods.

        Args:
            run_id: Unique identifier for this run.
            result: The completed RunResult.
            context: The RunContext for this run.
        """

    async def on_run_error(
        self,
        *,
        run_id: UUID,
        error: Exception,
        context: RunContext,
    ) -> None:
        """Called when an agent run fails with an exception.

        Called before the exception propagates to the caller.

        Args:
            run_id: Unique identifier for this run.
            error: The exception that caused the failure.
            context: The RunContext for this run.
        """

    async def on_tool_call(
        self,
        *,
        run_id: UUID,
        tool_name: str,
        arguments: dict[str, Any],
        context: RunContext,
    ) -> None:
        """Called before a tool is executed.

        Args:
            run_id: Unique identifier for the current run.
            tool_name: Name of the tool about to be called.
            arguments: Arguments passed to the tool.
            context: The RunContext for this run.
        """

    async def on_tool_result(
        self,
        *,
        run_id: UUID,
        tool_name: str,
        result: str,
        duration_ms: float,
        context: RunContext,
    ) -> None:
        """Called after a tool finishes executing.

        Args:
            run_id: Unique identifier for the current run.
            tool_name: Name of the tool that was called.
            result: Serialized result string from the tool.
            duration_ms: Execution time in milliseconds.
            context: The RunContext for this run.
        """

    # ------------------------------------------------------------------
    # Orchestration hooks
    # ------------------------------------------------------------------

    async def on_orchestration_start(
        self,
        *,
        run_id: UUID,
        user_input: str,
        orchestration_type: str,
        context: RunContext | None,
    ) -> None:
        """Called when an orchestration begins.

        Fires for Pipeline, Router, Parallel, Supervisor, Graph, and Swarm.

        Args:
            run_id: Unique identifier for this orchestration run.
            user_input: The user's input message.
            orchestration_type: The pattern name (e.g. "pipeline", "graph").
            context: The shared RunContext, if provided.
        """

    async def on_orchestration_end(
        self,
        *,
        run_id: UUID,
        result: RunResult,
        orchestration_type: str,
        context: RunContext | None,
    ) -> None:
        """Called when an orchestration completes successfully.

        Args:
            run_id: Unique identifier for this orchestration run.
            result: The ``RunResult`` with pattern-specific detail in
                    ``result.detail`` (e.g. ``OrchestrationDetail``,
                    ``GraphDetail``, ``SwarmDetail``).
            orchestration_type: The pattern name (e.g. ``"pipeline"``, ``"graph"``).
            context: The shared RunContext, if provided.
        """

    async def on_orchestration_error(
        self,
        *,
        run_id: UUID,
        error: Exception,
        orchestration_type: str,
        context: RunContext | None,
    ) -> None:
        """Called when an orchestration fails with an exception.

        Args:
            run_id: Unique identifier for this orchestration run.
            error: The exception that caused the failure.
            orchestration_type: The pattern name (e.g. "pipeline", "graph").
            context: The shared RunContext, if provided.
        """


async def _invoke_hooks(
    hooks: list[RunHooks],
    method_name: str,
    **kwargs: Any,
) -> None:
    """Call a hook method on all hooks, swallowing errors.

    Each hook is called in order. If a hook raises an exception,
    it is logged and the remaining hooks still execute.

    Args:
        hooks: List of hook instances.
        method_name: Name of the method to call (e.g., "on_run_start").
        **kwargs: Keyword arguments to pass to the hook method.
    """
    for hook in hooks:
        try:
            method = getattr(hook, method_name)
            await method(**kwargs)
        except Exception:
            logger.exception(
                "Hook %s.%s() failed",
                type(hook).__name__,
                method_name,
            )
