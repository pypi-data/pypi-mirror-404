"""Checkpoint storage for Tantra.

Provides state persistence for interrupted agent runs,
enabling async in-the-loop workflows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from ..types import Message


class Checkpoint(BaseModel):
    """Saved state of an interrupted agent run.

    Contains everything needed to resume execution after
    receiving human input.

    Attributes:
        id: Unique checkpoint identifier.
        run_id: ID of the interrupted agent run.
        session_id: Optional session identifier for grouping checkpoints.
        checkpoint_type: Type of checkpoint ("interrupt" or "progress").
        name: Name of the agent.
        messages: Conversation messages at the point of interruption.
        pending_tool: Name of the tool awaiting approval, if any.
        pending_args: Arguments for the pending tool call.
        pending_tool_call_id: Provider-assigned tool call ID.
        prompt: Human-readable prompt for the pending review.
        context: Additional context for the checkpoint.
        status: Current status (pending, completed, expired, aborted).
        created_at: When the checkpoint was created.
        expires_at: Optional expiration time for the checkpoint.
        response_value: Value from the human response, once provided.
        response_reason: Reason from the human response, once provided.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: UUID
    session_id: str | None = None
    checkpoint_type: str = (
        "interrupt"  # "interrupt" | "progress" | "graph_progress" | "graph_interrupt"
    )
    name: str
    messages: list[Message]
    pending_tool: str | None = None
    pending_args: dict[str, Any] = {}
    pending_tool_call_id: str | None = None
    prompt: str = ""
    context: dict[str, Any] = {}
    status: str = "pending"  # pending | completed | expired | aborted
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    response_value: Any = None
    response_reason: str | None = None


class CheckpointStore(ABC):
    """Abstract base class for checkpoint storage.

    Implement this to create custom storage backends.
    """

    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> str:
        """Save a checkpoint.

        Args:
            checkpoint: The checkpoint to save.

        Returns:
            The checkpoint ID.
        """
        pass

    @abstractmethod
    async def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            The checkpoint, or None if not found.
        """
        pass

    @abstractmethod
    async def update(self, checkpoint_id: str, **updates: Any) -> bool:
        """Update a checkpoint.

        Args:
            checkpoint_id: The checkpoint ID.
            **updates: Fields to update.

        Returns:
            True if updated, False if not found.
        """
        pass

    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def list_pending(self, name: str | None = None) -> list[Checkpoint]:
        """List pending checkpoints.

        Args:
            name: Optional filter by agent name.

        Returns:
            List of pending checkpoints.
        """
        pass

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
        return []

    async def cleanup_expired(self) -> int:
        """Delete expired checkpoints.

        Returns:
            Number of checkpoints deleted.
        """
        return 0
