"""Agent registry for Tantra.

Provides a way to register and retrieve agents by ID,
enabling checkpoint resume functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agent import Agent


class AgentRegistry:
    """Registry of agents by ID.

    Used to reconstruct agents when resuming from checkpoints.
    Agents must be registered before they can be resumed.

    Examples:
        ```python
        registry = AgentRegistry()

        # Register an agent
        agent = Agent("openai:gpt-4o", tools=tools)
        registry.register("support-agent", agent)

        # Later, resume from checkpoint
        agent = registry.get("support-agent")
        result = await agent.resume(checkpoint_id)
        ```
    """

    _instance: AgentRegistry | None = None

    def __init__(self):
        """Initialize an empty agent registry."""
        self._agents: dict[str, Agent] = {}

    @classmethod
    def get_instance(cls) -> AgentRegistry:
        """Get the global registry instance.

        Returns:
            The singleton AgentRegistry.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, agent: Agent) -> None:
        """Register an agent.

        Args:
            name: Unique identifier for the agent.
            agent: The agent instance.
        """
        self._agents[name] = agent
        # Set the agent's name so it knows its own identity
        agent._name = name

    def get(self, name: str) -> Agent | None:
        """Get an agent by ID.

        Args:
            name: The agent ID.

        Returns:
            The agent, or None if not found.
        """
        return self._agents.get(name)

    def unregister(self, name: str) -> bool:
        """Remove an agent from the registry.

        Args:
            name: The agent ID.

        Returns:
            True if removed, False if not found.
        """
        if name in self._agents:
            del self._agents[name]
            return True
        return False

    def list_agents(self) -> list[str]:
        """List all registered agent IDs.

        Returns:
            List of registered agent ID strings.
        """
        return list(self._agents.keys())

    def clear(self) -> None:
        """Remove all agents from the registry."""
        self._agents.clear()


# Global registry instance
default_registry = AgentRegistry.get_instance()


def register_agent(name: str, agent: Agent) -> None:
    """Register an agent in the global registry.

    Args:
        name: Unique identifier for the agent.
        agent: The agent instance to register.
    """
    default_registry.register(name, agent)


def get_agent(name: str) -> Agent | None:
    """Get an agent from the global registry.

    Args:
        name: The agent ID to look up.

    Returns:
        The agent, or None if not found.
    """
    return default_registry.get(name)
