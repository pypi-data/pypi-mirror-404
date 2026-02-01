"""Request and response models for the Tantra serve module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from tantra.types import RunMetadata


class RunRequest(BaseModel):
    """Request body for starting a run.

    Attributes:
        message: The user message to send to the runnable.
        session_id: Optional memory continuity key. If omitted, the server
            auto-generates a UUID so every run has persistent memory.
            Reuse the same ``session_id`` across runs for conversation continuity.
        stream: Whether to stream the response via SSE.
    """

    message: str = Field(description="The user message to send to the runnable.")
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for memory continuity. Auto-generated if omitted.",
    )
    stream: bool = Field(default=False, description="Stream response via SSE.")


class InterruptResponsePayload(BaseModel):
    """Payload for responding to an interrupted run.

    Attributes:
        value: The human's response value (e.g. ``"yes"``, ``"approved"``).
        proceed: Whether to proceed with the pending tool execution.
        reason: Optional reason for the decision.
    """

    value: Any = Field(default=None, description="The human's response value.")
    proceed: bool = Field(default=True, description="Whether to proceed with the pending tool.")
    reason: str | None = Field(default=None, description="Optional reason for the decision.")


class ResumeRequest(BaseModel):
    """Request body for resuming from a checkpoint.

    Attributes:
        checkpoint_id: The checkpoint to resume from.
        response: Required for interrupt checkpoints — the human's response.
        stream: Whether to stream the response via SSE.
    """

    checkpoint_id: str = Field(description="The checkpoint ID to resume from.")
    response: InterruptResponsePayload | None = Field(
        default=None,
        description="Human response for interrupt checkpoints.",
    )
    stream: bool = Field(default=False, description="Stream response via SSE.")


class RunResponse(BaseModel):
    """Unified response for ``/runs`` and ``/resume`` endpoints.

    The ``status`` field indicates the outcome:

    - ``"completed"`` — run finished, ``output`` and ``metadata`` are populated.
    - ``"interrupted"`` — a tool requires human input, ``checkpoint_id`` and
      ``prompt`` are populated. Call ``/resume`` with the checkpoint ID.
    - ``"failed"`` — an error occurred, ``error`` is populated.

    Attributes:
        run_id: Unique identifier for this execution.
        session_id: Session ID (auto-generated or echoed from request).
        status: One of ``"completed"``, ``"interrupted"``, or ``"failed"``.
        output: The final text response (when completed).
        metadata: Token usage, cost, and timing metadata (when completed).
        detail: Serialized orchestration detail — execution path, node outputs,
            handoff chain, etc. (when completed, for orchestrators).
        checkpoint_id: Checkpoint to resume from (when interrupted).
        prompt: The interrupt prompt to show the user (when interrupted).
        error: Error message (when failed).
    """

    run_id: str = Field(description="Unique identifier for this execution.")
    session_id: str = Field(description="Session ID (auto-generated or echoed from request).")
    status: str = Field(description="Outcome: 'completed', 'interrupted', or 'failed'.")
    output: str | None = Field(default=None, description="The final text response.")
    metadata: RunMetadata | None = Field(default=None, description="Run metadata.")
    detail: dict[str, Any] | None = Field(
        default=None, description="Serialized orchestration detail."
    )
    checkpoint_id: str | None = Field(
        default=None, description="Checkpoint ID (when interrupted)."
    )
    prompt: str | None = Field(default=None, description="Interrupt prompt (when interrupted).")
    error: str | None = Field(default=None, description="Error message (when failed).")


class CheckpointSummary(BaseModel):
    """Summary of a checkpoint for listing endpoints.

    Attributes:
        id: Unique checkpoint identifier.
        run_id: The run that created this checkpoint.
        session_id: Session the checkpoint belongs to.
        checkpoint_type: Type of checkpoint (e.g. ``"graph_progress"``).
        name: Runnable name.
        status: Checkpoint status (``"pending"``, ``"completed"``, etc.).
        created_at: ISO timestamp of checkpoint creation.
    """

    id: str = Field(description="Unique checkpoint identifier.")
    run_id: str = Field(description="The run that created this checkpoint.")
    session_id: str | None = Field(default=None, description="Session ID.")
    checkpoint_type: str = Field(description="Type of checkpoint.")
    name: str = Field(description="Runnable name.")
    status: str = Field(description="Checkpoint status.")
    created_at: str = Field(description="ISO timestamp of creation.")


class RunnableInfo(BaseModel):
    """Summary information about a served runnable.

    Attributes:
        name: Unique identifier for the runnable.
        has_system_prompt: Whether the runnable has a system prompt configured.
        tools: List of tool names available to the runnable.
    """

    name: str = Field(description="Unique identifier for the runnable.")
    has_system_prompt: bool = Field(
        description="Whether the runnable has a system prompt configured."
    )
    tools: list[str] = Field(description="List of tool names available to the runnable.")


class HealthResponse(BaseModel):
    """Response body for health check endpoint.

    Attributes:
        status: Service health status string (default ``"ok"``).
        runnables: List of registered runnable names.
    """

    status: str = Field(default="ok", description="Service health status.")
    runnables: list[str] = Field(description="List of registered runnable names.")
