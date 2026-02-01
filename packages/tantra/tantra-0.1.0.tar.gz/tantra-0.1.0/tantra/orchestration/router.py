"""Router orchestration pattern.

Routes requests to the appropriate agent based on content analysis.
Supports both function-based and LLM-based routing.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ..context import ContextStore, MemoryContextStore, RunContext
from ..hooks import RunHooks, _invoke_hooks
from ..observability import Logger, trace_orchestration_run
from ..types import LogType, RunMetadata, RunResult
from .base import AgentStep, OrchestrationDetail, Orchestrator, resolve_context, save_context

if TYPE_CHECKING:
    from ..agent import Agent


class Router(Orchestrator):
    """Routes requests to the appropriate agent.

    Uses a routing function or LLM to determine which agent handles a request.
    Useful for specialized agents that handle different types of queries.

    Examples:
        ```python
        def route_by_topic(user_input: str) -> str:
            if "billing" in user_input.lower():
                return "billing"
            elif "technical" in user_input.lower():
                return "technical"
            return "general"

        router = Router(
            agents={
                "billing": billing_agent,
                "technical": tech_agent,
                "general": general_agent,
            },
            route_fn=route_by_topic,
            default="general",
        )

        result = await router.run("I have a billing question")
        # Routes to billing_agent
        ```
    """

    def __init__(
        self,
        agents: dict[str, Agent],
        route_fn: Callable[[str], str] | None = None,
        router_agent: Agent | None = None,
        default: str | None = None,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
        name: str | None = None,
    ):
        """Initialize router.

        Args:
            agents: Dict mapping names to agents.
            route_fn: Function that returns agent name for given input.
            router_agent: Optional agent to do LLM-based routing.
            default: Default agent name if routing fails.
            context_store: Optional store for persisting shared context across runs.
            hooks: Optional list of RunHooks for lifecycle notifications.
            name: Optional human-readable name for this orchestrator.

        Raises:
            ValueError: If neither route_fn nor router_agent is provided.
        """
        self._name = name
        self._context_store: ContextStore = context_store or MemoryContextStore()
        self._hooks: list[RunHooks] = hooks or []
        self._agents = agents
        self.route_fn = route_fn
        self.router_agent = router_agent
        self.default = default or (list(agents.keys())[0] if agents else None)

        if not route_fn and not router_agent:
            raise ValueError("Must provide either route_fn or router_agent")

    @property
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        return "router"

    @property
    def agents(self) -> dict[str, Agent]:
        """Get dict of agents."""
        return self._agents.copy()

    def clone(self, **kwargs: Any) -> Router:
        """Create a copy of this router with optional resource overrides.

        Args:
            **kwargs: Optional overrides. Recognised keys:
                ``context_store`` — session-scoped context store.

        Returns:
            A new Router sharing the same agents and routing logic.
        """
        return Router(
            agents=self._agents,
            route_fn=self.route_fn,
            router_agent=self.router_agent,
            default=self.default,
            context_store=kwargs.get("context_store", self._context_store),
            hooks=self._hooks,
            name=self._name,
        )

    async def route(
        self,
        user_input: str,
        parent_run_id: UUID | None = None,
        logger: Logger | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Determine which agent should handle the input.

        Args:
            user_input: The input to route.
            parent_run_id: Optional parent run ID for trace correlation.
            logger: Optional logger for recording routing decisions.

        Returns:
            Tuple of (name, routing_metadata).
        """
        routing_metadata: dict[str, Any] = {"method": "unknown"}

        if self.route_fn:
            name = self.route_fn(user_input)
            routing_metadata = {
                "method": "function",
                "selected_agent": name,
            }
            if logger:
                logger.log(
                    LogType.TOOL_CALL,
                    data={
                        "event": "routing",
                        "method": "function",
                        "selected_agent": name,
                    },
                )
            return name, routing_metadata

        if self.router_agent:
            # Use LLM-based routing
            agent_list = ", ".join(self._agents.keys())
            prompt = f"""Given the following input, which agent should handle it?
Available agents: {agent_list}

Input: {user_input}

Respond with just the agent name, nothing else."""

            # Log the routing LLM call
            if logger:
                logger.log(
                    LogType.TOOL_CALL,
                    data={
                        "event": "routing",
                        "method": "llm",
                        "available_agents": list(self._agents.keys()),
                    },
                )

            result = await self.router_agent.run(prompt, parent_run_id=parent_run_id)
            llm_choice = result.output.strip().lower()

            # Find matching agent
            selected_agent = self.default
            for agent_name in self._agents:
                if agent_name.lower() == llm_choice:
                    selected_agent = agent_name
                    break

            routing_metadata = {
                "method": "llm",
                "llm_response": result.output.strip(),
                "selected_agent": selected_agent,
                "tokens_used": result.metadata.total_tokens,
            }

            # Log the routing decision
            if logger:
                logger.log(
                    LogType.TOOL_RESULT,
                    data={
                        "event": "routing_decision",
                        "llm_response": result.output.strip(),
                        "selected_agent": selected_agent,
                    },
                    metadata={"tokens_used": result.metadata.total_tokens},
                )

            return selected_agent, routing_metadata

        return self.default, {"method": "default", "selected_agent": self.default}

    @trace_orchestration_run("router")
    async def run(
        self,
        user_input: str,
        run_id: UUID | None = None,
        shared_context: RunContext | None = None,
        session_id: str | None = None,
    ) -> RunResult[OrchestrationDetail]:
        """Route input to the appropriate agent and execute it.

        Args:
            user_input: The input to route and process.
            run_id: Optional run ID for trace correlation.
            shared_context: Optional RunContext shared across agents.
            session_id: Optional session ID for persisting shared context.

        Returns:
            RunResult with OrchestrationDetail containing step details.

        Raises:
            Exception: Propagated from agent execution; recorded in the step.
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

        logger = Logger(run_id=orchestration_id)
        logger.start_run()

        # Log router start
        logger.log(
            LogType.PROMPT,
            data={"input": user_input, "available_agents": list(self._agents.keys())},
            metadata={"router_execution": True},
        )

        steps: list[AgentStep] = []
        start_time = datetime.now(UTC)

        # Determine route (with logging)
        name, routing_metadata = await self.route(
            user_input, parent_run_id=orchestration_id, logger=logger
        )

        if name not in self._agents:
            name = self.default

        agent = self._agents[name]

        try:
            result = await agent.run(user_input, parent_run_id=orchestration_id, context=ctx)

            step = AgentStep(
                agent_id=name,
                input=user_input,
                output=result.output,
                metadata=result.metadata,
                duration_ms=result.metadata.duration_ms,
            )
            steps.append(step)

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
                duration_ms=0,
                error=e,
            )
            steps.append(step)

        total_duration = (datetime.now(UTC) - start_time).total_seconds() * 1000

        await save_context(self._context_store, ctx, session_id)

        orch_result = RunResult(
            output=steps[0].output if steps else "",
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


def select(
    agents: dict[str, Agent],
    route_fn: Callable[[str], str],
    default: str | None = None,
) -> Router:
    """Create a router with a routing function.

    Convenience function for quick router creation.

    Args:
        agents: Dict mapping names to agents.
        route_fn: Function that returns the agent name for a given input.
        default: Default agent name if routing fails.

    Returns:
        Router configured with the given agents and routing function.

    Examples:
        ```python
        router = select(
            {"a": agent_a, "b": agent_b},
            route_fn=lambda x: "a" if "foo" in x else "b",
        )
        ```
    """
    return Router(agents=agents, route_fn=route_fn, default=default)
