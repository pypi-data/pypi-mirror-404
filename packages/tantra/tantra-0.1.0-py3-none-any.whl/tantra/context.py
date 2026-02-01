"""Shared execution context for Tantra agent runs.

RunContext is a mutable key-value store that tools can read/write
during execution, enabling tool-to-tool data sharing without going
through the LLM.

Example:
    from tantra import Agent, RunContext, ToolSet, tool

    @tool
    def step_one(query: str, context: RunContext) -> str:
        context.set("data", fetch_data(query))
        return "Data fetched"

    @tool
    def step_two(context: RunContext) -> str:
        data = context.get("data")
        return f"Processed {len(data)} items"

    agent = Agent("openai:gpt-4o", tools=ToolSet([step_one, step_two]))
    result = await agent.run("Analyze sales data")
    print(result.context.to_dict())
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RunContext:
    """Shared mutable state accessible by tools during a run.

    Tools opt in by declaring a ``context: RunContext`` parameter::

        @tool
        def my_tool(arg: str, context: RunContext) -> str:
            previous = context.get("last_result", "nothing")
            context.set("last_result", arg)
            return f"Got {arg}, previous was {previous}"

    The context parameter is automatically injected by the engine—it is
    excluded from the JSON schema sent to the LLM.

    A fresh RunContext is created for each ``agent.run()`` call. To persist
    context across runs, pass a ``session_id``::

        result = await agent.run("query", session_id="sess_123")

    The context is available after the run via ``result.context``.

    .. note::
        **Parallel tool safety:** When ``parallel_tool_execution=True``
        (the default), multiple tools may run concurrently within a single
        agent run. All parallel tools share the same RunContext instance.
        Individual ``.get()`` and ``.set()`` calls are safe (Python's GIL
        ensures dict operations are atomic), but read-then-write sequences
        are not atomic::

            # NOT safe in parallel — another tool may write between get and set
            val = context.get("counter", 0)
            context.set("counter", val + 1)

        If your tools need to coordinate writes to the same keys, either
        set ``parallel_tool_execution=False`` on the Agent, or use
        distinct keys per tool.
    """

    def __init__(self, initial: dict[str, Any] | None = None):
        """Initialize a RunContext.

        Args:
            initial: Optional initial key-value data to populate the context.
        """
        self._data: dict[str, Any] = dict(initial) if initial else {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key.

        Args:
            key: The key to look up.
            default: Value to return if key is not found.

        Returns:
            The stored value, or *default* if the key does not exist.
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value by key.

        Args:
            key: The key to store under.
            value: The value to store.
        """
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Check whether *key* exists in the context."""
        return key in self._data

    def to_dict(self) -> dict[str, Any]:
        """Return a shallow copy of the context data.

        Returns:
            A new dict with the same keys and values.
        """
        return self._data.copy()

    def copy(self) -> RunContext:
        """Return a shallow copy of this context.

        Returns:
            A new RunContext with the same key-value data.
        """
        return RunContext(self._data.copy())

    def clear(self) -> None:
        """Clear all context data."""
        self._data.clear()

    def __repr__(self) -> str:
        return f"RunContext({self._data})"


class ContextStore(ABC):
    """Abstract base class for persisting context across runs by session ID.

    Implement this to store context in SQLite, Redis, a database, etc.
    """

    @abstractmethod
    async def load(self, session_id: str) -> dict[str, Any]:
        """Load context data for a session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The stored context data, or an empty dict if not found.
        """
        ...

    @abstractmethod
    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        """Save context data for a session.

        Args:
            session_id: Unique identifier for the session.
            data: Context data to persist.
        """
        ...


class MemoryContextStore(ContextStore):
    """In-memory context store. Data is lost on process restart.

    This is the default store used by Agent.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    async def load(self, session_id: str) -> dict[str, Any]:
        """Load context data for a session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            A copy of the stored data, or an empty dict if the session is new.
        """
        return dict(self._sessions.get(session_id, {}))

    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        """Save context data for a session.

        Args:
            session_id: Unique identifier for the session.
            data: Context data to persist (a copy is stored).
        """
        self._sessions[session_id] = dict(data)
