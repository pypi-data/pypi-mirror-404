"""PostgreSQL-backed checkpoint store for Tantra.

Provides persistent checkpoint storage using PostgreSQL via asyncpg.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import asyncpg

from ..types import Message
from .base import Checkpoint, CheckpointStore


class PostgresCheckpointStore(CheckpointStore):
    """PostgreSQL-backed checkpoint store.

    The table is auto-created on first use.

    Examples:
        ```python
        pool = await asyncpg.create_pool(dsn="postgresql://...")
        store = PostgresCheckpointStore(pool)
        ```
    """

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS tantra_checkpoints (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        session_id TEXT,
        checkpoint_type TEXT DEFAULT 'interrupt',
        name TEXT,
        status TEXT DEFAULT 'pending',
        messages JSONB NOT NULL,
        pending_tool TEXT,
        pending_args JSONB,
        pending_tool_call_id TEXT,
        prompt TEXT,
        context JSONB,
        created_at TIMESTAMPTZ DEFAULT now(),
        expires_at TIMESTAMPTZ,
        response_value JSONB,
        response_reason TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_tantra_checkpoints_status
        ON tantra_checkpoints(status);
    CREATE INDEX IF NOT EXISTS idx_tantra_checkpoints_agent
        ON tantra_checkpoints(name);
    CREATE INDEX IF NOT EXISTS idx_tantra_checkpoints_session
        ON tantra_checkpoints(session_id);
    """

    MIGRATION_DDL = """
    ALTER TABLE tantra_checkpoints ADD COLUMN IF NOT EXISTS session_id TEXT;
    ALTER TABLE tantra_checkpoints ADD COLUMN IF NOT EXISTS checkpoint_type TEXT DEFAULT 'interrupt';
    CREATE INDEX IF NOT EXISTS idx_tantra_checkpoints_session
        ON tantra_checkpoints(session_id);
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        """Initialize PostgresCheckpointStore.

        Args:
            pool: asyncpg connection pool.
        """
        self._pool = pool
        self._table_ready = False

    async def _ensure_table(self) -> None:
        """Create the checkpoints table if it doesn't exist."""
        if self._table_ready:
            return
        async with self._pool.acquire() as conn:
            await conn.execute(self.TABLE_DDL)
            await conn.execute(self.MIGRATION_DDL)
        self._table_ready = True

    async def save(self, checkpoint: Checkpoint) -> str:
        """Save a checkpoint to Postgres.

        Args:
            checkpoint: The checkpoint to save.

        Returns:
            The checkpoint ID.
        """
        await self._ensure_table()

        messages_json = json.dumps([m.model_dump(mode="json") for m in checkpoint.messages])
        pending_args_json = json.dumps(checkpoint.pending_args) if checkpoint.pending_args else None
        context_json = json.dumps(checkpoint.context) if checkpoint.context else None

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tantra_checkpoints
                    (id, run_id, session_id, checkpoint_type, name, status,
                     messages, pending_tool, pending_args, pending_tool_call_id,
                     prompt, context, created_at, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    messages = EXCLUDED.messages,
                    pending_tool = EXCLUDED.pending_tool,
                    pending_args = EXCLUDED.pending_args,
                    pending_tool_call_id = EXCLUDED.pending_tool_call_id,
                    prompt = EXCLUDED.prompt,
                    context = EXCLUDED.context,
                    expires_at = EXCLUDED.expires_at
                """,
                checkpoint.id,
                str(checkpoint.run_id),
                checkpoint.session_id,
                checkpoint.checkpoint_type,
                checkpoint.name,
                checkpoint.status,
                messages_json,
                checkpoint.pending_tool,
                pending_args_json,
                checkpoint.pending_tool_call_id,
                checkpoint.prompt,
                context_json,
                checkpoint.created_at,
                checkpoint.expires_at,
            )

        return checkpoint.id

    async def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint from Postgres.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            The checkpoint, or None if not found.
        """
        await self._ensure_table()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tantra_checkpoints WHERE id = $1",
                checkpoint_id,
            )

        if row is None:
            return None

        return self._row_to_checkpoint(row)

    async def update(self, checkpoint_id: str, **updates: Any) -> bool:
        """Update a checkpoint in Postgres.

        Args:
            checkpoint_id: The checkpoint ID.
            **updates: Fields to update (e.g., status, response_value).

        Returns:
            True if updated, False if not found.
        """
        await self._ensure_table()

        if not updates:
            return False

        # Build SET clause dynamically
        set_parts: list[str] = []
        values: list[Any] = []
        idx = 1

        for key, value in updates.items():
            if key == "response_value":
                set_parts.append(f"response_value = ${idx}")
                values.append(json.dumps(value) if value is not None else None)
            elif key == "context":
                set_parts.append(f"context = ${idx}")
                values.append(json.dumps(value) if value is not None else None)
            else:
                set_parts.append(f"{key} = ${idx}")
                values.append(value)
            idx += 1

        values.append(checkpoint_id)
        set_clause = ", ".join(set_parts)

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                f"UPDATE tantra_checkpoints SET {set_clause} WHERE id = ${idx}",
                *values,
            )

        return result.endswith("1")

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint from Postgres.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        await self._ensure_table()

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM tantra_checkpoints WHERE id = $1",
                checkpoint_id,
            )

        return result.endswith("1")

    async def list_pending(self, name: str | None = None) -> list[Checkpoint]:
        """List pending checkpoints.

        Args:
            name: Optional filter by agent name.

        Returns:
            List of pending checkpoints.
        """
        await self._ensure_table()

        async with self._pool.acquire() as conn:
            if name is not None:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tantra_checkpoints
                    WHERE status = 'pending' AND name = $1
                    ORDER BY created_at
                    """,
                    name,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tantra_checkpoints
                    WHERE status = 'pending'
                    ORDER BY created_at
                    """
                )

        return [self._row_to_checkpoint(row) for row in rows]

    async def list_by_name(
        self,
        name: str,
        session_id: str | None = None,
        status: str | None = None,
    ) -> list[Checkpoint]:
        """List checkpoints filtered by runnable name and optional criteria.

        Args:
            name: Runnable name to filter by (required).
            session_id: Optional filter by session ID.
            status: Optional filter by status (e.g. ``"pending"``).

        Returns:
            List of matching checkpoints, ordered by creation time.
        """
        await self._ensure_table()

        conditions = ["name = $1"]
        values: list[Any] = [name]
        idx = 2

        if session_id is not None:
            conditions.append(f"session_id = ${idx}")
            values.append(session_id)
            idx += 1

        if status is not None:
            conditions.append(f"status = ${idx}")
            values.append(status)
            idx += 1

        where = " AND ".join(conditions)
        query = f"SELECT * FROM tantra_checkpoints WHERE {where} ORDER BY created_at"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *values)

        return [self._row_to_checkpoint(row) for row in rows]

    async def cleanup_expired(self) -> int:
        """Delete expired checkpoints.

        Returns:
            Number of checkpoints deleted.
        """
        await self._ensure_table()

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM tantra_checkpoints
                WHERE expires_at IS NOT NULL AND expires_at < $1
                """,
                datetime.now(UTC),
            )

        # Parse "DELETE N" from result
        try:
            return int(result.split()[-1])
        except (ValueError, IndexError):
            return 0

    @staticmethod
    def _row_to_checkpoint(row: asyncpg.Record) -> Checkpoint:
        """Convert a database row to a Checkpoint.

        Args:
            row: asyncpg Record from the tantra_checkpoints table.

        Returns:
            Checkpoint instance.
        """
        messages_data = (
            json.loads(row["messages"]) if isinstance(row["messages"], str) else row["messages"]
        )
        messages = [Message(**m) for m in messages_data]

        pending_args = {}
        if row["pending_args"]:
            pending_args = (
                json.loads(row["pending_args"])
                if isinstance(row["pending_args"], str)
                else row["pending_args"]
            )

        context = {}
        if row["context"]:
            context = (
                json.loads(row["context"]) if isinstance(row["context"], str) else row["context"]
            )

        response_value = None
        if row["response_value"]:
            response_value = (
                json.loads(row["response_value"])
                if isinstance(row["response_value"], str)
                else row["response_value"]
            )

        return Checkpoint(
            id=row["id"],
            run_id=UUID(row["run_id"]),
            session_id=row.get("session_id"),
            checkpoint_type=row.get("checkpoint_type", "interrupt"),
            name=row["name"] or "",
            messages=messages,
            pending_tool=row["pending_tool"],
            pending_args=pending_args,
            pending_tool_call_id=row["pending_tool_call_id"],
            prompt=row["prompt"] or "",
            context=context,
            status=row["status"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            response_value=response_value,
            response_reason=row["response_reason"],
        )
