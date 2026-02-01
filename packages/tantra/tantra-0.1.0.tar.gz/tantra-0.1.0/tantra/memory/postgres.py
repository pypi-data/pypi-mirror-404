"""PostgreSQL-backed memory for Tantra.

Provides persistent conversation memory using PostgreSQL via asyncpg.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import asyncpg

from ..types import Message
from .base import Memory


class PostgresMemory(Memory):
    """PostgreSQL-backed conversation memory.

    Uses an asyncpg connection pool. Messages are cached locally for
    synchronous access and persisted to Postgres.

    The table is auto-created on first use via :meth:`create`.

    Examples:
        ```python
        pool = await asyncpg.create_pool(dsn="postgresql://...")
        memory = await PostgresMemory.create(pool, session_key="user-123:agent-1")
        ```
    """

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS tantra_messages (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_key TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT,
        tool_call_id TEXT,
        tool_calls JSONB,
        name TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_tantra_messages_session
        ON tantra_messages(session_key, created_at);
    """

    def __init__(self, pool: asyncpg.Pool, session_key: str) -> None:
        """Initialize PostgresMemory.

        Prefer using :meth:`create` to also load existing messages
        and ensure the table exists.

        Args:
            pool: asyncpg connection pool.
            session_key: Key identifying this conversation session.
        """
        self._pool = pool
        self._session_key = session_key
        self._messages: list[Message] = []
        self._table_ready = False

    @classmethod
    async def create(
        cls,
        pool: asyncpg.Pool,
        session_key: str,
    ) -> PostgresMemory:
        """Create a PostgresMemory instance, ensuring the table exists
        and loading any existing messages.

        Args:
            pool: asyncpg connection pool.
            session_key: Key identifying this conversation session.

        Returns:
            Initialized PostgresMemory with messages loaded from Postgres.
        """
        memory = cls(pool, session_key)
        await memory._ensure_table()
        await memory._load_messages()
        return memory

    async def _ensure_table(self) -> None:
        """Create the messages table if it doesn't exist."""
        if self._table_ready:
            return
        async with self._pool.acquire() as conn:
            await conn.execute(self.TABLE_DDL)
        self._table_ready = True

    async def _load_messages(self) -> None:
        """Load messages from Postgres into local cache."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content, tool_call_id, tool_calls, name
                FROM tantra_messages
                WHERE session_key = $1
                ORDER BY created_at
                """,
                self._session_key,
            )

        self._messages = []
        for row in rows:
            kwargs: dict[str, Any] = {
                "role": row["role"],
                "content": row["content"],
            }
            if row["tool_call_id"]:
                kwargs["tool_call_id"] = row["tool_call_id"]
            if row["tool_calls"]:
                from ..types import ToolCallData

                kwargs["tool_calls"] = [ToolCallData(**tc) for tc in json.loads(row["tool_calls"])]
            if row["name"]:
                kwargs["name"] = row["name"]
            self._messages.append(Message(**kwargs))

    def add_message(self, message: Message) -> None:
        """Add a message to memory and persist to Postgres.

        The message is added to the local cache immediately. The Postgres
        insert is scheduled as a fire-and-forget task on the running
        event loop.

        Args:
            message: The message to store.
        """
        self._messages.append(message)

        # Schedule async insert on the running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._insert_message(message))
        except RuntimeError:
            # No running loop — skip async persistence
            pass

    async def _insert_message(self, message: Message) -> None:
        """Insert a single message into Postgres."""
        tool_calls_json = None
        if message.tool_calls:
            tool_calls_json = json.dumps([tc.model_dump() for tc in message.tool_calls])

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tantra_messages (session_key, role, content, tool_call_id, tool_calls, name)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                self._session_key,
                message.role,
                message.content if isinstance(message.content, str) else None,
                message.tool_call_id,
                tool_calls_json,
                message.name,
            )

    def get_messages(self) -> list[Message]:
        """Get all messages from the local cache.

        Returns:
            List of messages in chronological order.
        """
        return list(self._messages)

    def clear(self) -> None:
        """Clear all messages from memory and Postgres.

        The local cache is cleared immediately. The Postgres DELETE is
        scheduled as a fire-and-forget task on the running event loop.
        """
        self._messages.clear()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._clear_postgres())
        except RuntimeError:
            pass

    async def _clear_postgres(self) -> None:
        """Delete all messages for this session from Postgres."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM tantra_messages WHERE session_key = $1",
                self._session_key,
            )

    @property
    def session_key(self) -> str:
        """The session key for this memory instance."""
        return self._session_key
