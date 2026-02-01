"""RunnableFactory for constructing session-isolated orchestrators.

Provides the factory pattern for RunnableServer, enabling session-isolated
agents with pluggable storage backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .models import RunnableInfo

if TYPE_CHECKING:
    from ..checkpoints import CheckpointStore
    from ..orchestration.base import Orchestrator


class RunnableFactory(ABC):
    """Abstract factory for creating session-isolated orchestrators.

    A factory manages a set of named orchestrator templates and produces
    session-isolated instances on demand.
    """

    @property
    @abstractmethod
    def names(self) -> list[str]:
        """List of available runnable names."""
        ...

    @abstractmethod
    async def get(self, name: str, session_id: str) -> Orchestrator:
        """Get or construct a session-isolated Orchestrator.

        Args:
            name: The registered runnable name.
            session_id: Client session ID for memory isolation.

        Returns:
            An Orchestrator instance isolated to this session.

        Raises:
            KeyError: If the name is not registered.
        """
        ...

    @abstractmethod
    def list_runnables(self) -> list[RunnableInfo]:
        """Return summary info for all available runnables.

        Returns:
            List of RunnableInfo summaries.
        """
        ...

    @property
    def checkpoint_store(self) -> CheckpointStore | None:
        """Optional checkpoint store for listing/loading checkpoints.

        Returns None by default. Implementations with checkpoint support
        should override this property.
        """
        return None


class PostgresRunnableFactory(RunnableFactory):
    """Factory that uses PostgreSQL for session memory and checkpoints.

    Each call to :meth:`get` creates a fresh clone with a
    :class:`~tantra.memory.postgres.PostgresMemory` and
    :class:`~tantra.checkpoints.postgres.PostgresCheckpointStore`.
    No in-memory session cache — the memory is loaded from Postgres each
    time, so sessions survive server restarts.
    """

    def __init__(self, templates: dict[str, Orchestrator], pool: Any) -> None:
        """Initialize with named orchestrator templates and an asyncpg pool.

        Args:
            templates: Dict mapping names to orchestrator templates.
            pool: An asyncpg connection pool.
        """
        from ..checkpoints.postgres import PostgresCheckpointStore

        self._templates = templates
        self._pool = pool
        self._checkpoint_store = PostgresCheckpointStore(pool)

    @property
    def names(self) -> list[str]:
        """List of available runnable names."""
        return list(self._templates.keys())

    @property
    def checkpoint_store(self) -> CheckpointStore:
        """The shared PostgreSQL checkpoint store."""
        return self._checkpoint_store

    async def get(self, name: str, session_id: str) -> Orchestrator:
        """Get a session-isolated clone backed by Postgres.

        Args:
            name: The registered runnable name.
            session_id: Client session ID for memory isolation.

        Returns:
            A cloned Orchestrator instance with Postgres-backed memory.

        Raises:
            KeyError: If the name is not registered.
        """
        if name not in self._templates:
            raise KeyError(f"'{name}' not found")

        from ..memory.postgres import PostgresMemory

        template = self._templates[name]
        session_key = f"{name}:{session_id}"
        memory = await PostgresMemory.create(self._pool, session_key)
        return template.clone(memory=memory, checkpoint_store=self._checkpoint_store)

    def list_runnables(self) -> list[RunnableInfo]:
        """Return summary info for all available runnables.

        Returns:
            List of RunnableInfo summaries.
        """
        result = []
        for name, runnable in self._templates.items():
            tool_names = []
            if hasattr(runnable, "tools") and runnable.tools:
                tool_names = runnable.tools.names
            result.append(
                RunnableInfo(
                    name=name,
                    has_system_prompt=bool(getattr(runnable, "system_prompt", "")),
                    tools=tool_names,
                )
            )
        return result
