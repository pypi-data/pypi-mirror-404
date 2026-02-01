"""Solo orchestrator — wraps a single Agent for serving.

Provides the Orchestrator interface around a single Agent, enabling it
to be served via ``serve()`` with unified StreamEvent streaming.

Example::

    from tantra import Agent
    from tantra.orchestration import Solo

    agent = Agent("openai:gpt-4o", system_prompt="You are helpful.")
    solo = Solo(agent)
    result = await solo.run("Hello!")

    # Or let serve() auto-wrap:
    from tantra.serve import serve
    app = serve(agent)  # automatically wraps in Solo
"""

from __future__ import annotations

from typing import Any

from ..agent import Agent
from ..types import RunResult
from .base import Orchestrator


class Solo(Orchestrator):
    """Orchestrator that wraps a single Agent.

    Uses ``on_event=self._emit_step`` so agent-level events (tokens,
    tool_call, tool_result) bubble up into the unified stream.
    """

    def __init__(self, agent: Agent, *, name: str | None = None) -> None:
        """Initialize the Solo orchestrator.

        Args:
            agent: The Agent to wrap.
            name: Optional name override. Defaults to the agent's name.
        """
        self._agent = agent
        self._name = name or agent.name

    @property
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        return "solo"

    async def run(self, user_input: str, **kwargs: Any) -> RunResult:
        """Run the wrapped agent.

        Passes ``on_event=self._emit_step`` so that when streaming is
        active, token and tool events flow through to the stream queue.

        Args:
            user_input: The input to process.
            **kwargs: Passed through to agent.run().

        Returns:
            RunResult from the agent.
        """
        return await self._agent.run(user_input, on_event=self._active_on_event, **kwargs)

    async def resume(
        self, checkpoint_id: str, response: Any = None, **kwargs: Any
    ) -> RunResult:
        """Resume the wrapped agent from a checkpoint.

        Args:
            checkpoint_id: The checkpoint ID.
            response: The human's response.
            **kwargs: Additional arguments.

        Returns:
            RunResult from the resumed agent.
        """
        return await self._agent.resume(checkpoint_id, response, on_event=self._active_on_event, **kwargs)

    def clone(self, **kwargs: Any) -> Solo:
        """Create a copy with fresh agent state.

        Args:
            **kwargs: Passed to agent.clone().

        Returns:
            A new Solo with a cloned agent.
        """
        return Solo(self._agent.clone(**kwargs), name=self._name)

    @property
    def agent(self) -> Agent:
        """The wrapped agent."""
        return self._agent
