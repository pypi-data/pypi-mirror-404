"""Core types and data models for Tantra.

This module defines the fundamental data structures used throughout the framework.
All models use Pydantic for validation and serialization.
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, Discriminator, Field


class LogType(str, Enum):
    """Types of events in an agent execution trace."""

    PROMPT = "prompt"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"


class ToolCallData(BaseModel):
    """Represents a single tool call from the LLM.

    Attributes:
        id: Unique identifier for this tool call (provider-assigned).
        name: Name of the tool to invoke.
        arguments: Parsed arguments to pass to the tool function.
    """

    id: str = Field(description="Unique identifier for this tool call.")
    name: str = Field(description="Name of the tool to invoke.")
    arguments: dict[str, Any] = Field(description="Parsed arguments to pass to the tool.")


class TextContent(BaseModel):
    """A text content block within a message.

    Attributes:
        type: Discriminator field, always ``"text"``.
        text: The text content.
    """

    type: Literal["text"] = "text"
    text: str = Field(description="The text content.")


class ImageContent(BaseModel):
    """An image content block within a message.

    Represents an image via base64-encoded data or a URL.
    Only one of ``data`` or ``url`` should be set.
    """

    type: Literal["image"] = "image"
    data: str | None = Field(default=None, description="Base64-encoded image data.")
    url: str | None = Field(default=None, description="Image URL (passed to provider as-is).")
    media_type: str = Field(default="image/png", description="MIME type of the image.")
    detail: str | None = Field(
        default=None, description='Optional detail level hint (e.g. "low", "high" for OpenAI).'
    )

    @classmethod
    def from_file(cls, path: str | Path) -> ImageContent:
        """Create from a local image file.

        Reads the file, detects the MIME type from the extension, and
        base64-encodes the contents.

        Args:
            path: Path to the image file.

        Returns:
            An ImageContent with base64-encoded data and detected MIME type.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the MIME type cannot be determined as an image type.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None or not mime_type.startswith("image/"):
            raise ValueError(f"Cannot determine image MIME type for: {path}. Got: {mime_type}")

        raw_bytes = file_path.read_bytes()
        encoded = base64.b64encode(raw_bytes).decode("ascii")
        return cls(data=encoded, media_type=mime_type)

    @classmethod
    def from_url(
        cls, url: str, media_type: str = "image/png", detail: str | None = None
    ) -> ImageContent:
        """Create from an image URL.

        The URL is passed directly to the provider — no download occurs.

        Args:
            url: The image URL.
            media_type: MIME type of the image.
            detail: Optional detail level hint (e.g. ``"low"``, ``"high"`` for OpenAI).

        Returns:
            An ImageContent with the URL reference.
        """
        return cls(url=url, media_type=media_type, detail=detail)

    @classmethod
    def from_bytes(cls, data: bytes, media_type: str = "image/png") -> ImageContent:
        """Create from raw image bytes.

        Args:
            data: Raw image bytes.
            media_type: MIME type of the image.

        Returns:
            An ImageContent with base64-encoded data.
        """
        encoded = base64.b64encode(data).decode("ascii")
        return cls(data=encoded, media_type=media_type)


class FileContent(BaseModel):
    """A file content block within a message.

    Represents an arbitrary file (PDF, CSV, text, etc.) via base64-encoded data.
    Provider support for specific file types will vary.
    """

    type: Literal["file"] = "file"
    data: str = Field(description="Base64-encoded file data.")
    media_type: str = Field(description="MIME type of the file (e.g. 'application/pdf').")
    filename: str | None = Field(default=None, description="Optional original filename.")

    @classmethod
    def from_file(cls, path: str | Path) -> FileContent:
        """Create from a local file.

        Reads the file, detects the MIME type from the extension, and
        base64-encodes the contents.

        Args:
            path: Path to the file.

        Returns:
            A FileContent with base64-encoded data and detected MIME type.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the MIME type cannot be determined.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            raise ValueError(f"Cannot determine MIME type for: {path}")

        raw_bytes = file_path.read_bytes()
        encoded = base64.b64encode(raw_bytes).decode("ascii")
        return cls(data=encoded, media_type=mime_type, filename=file_path.name)

    @classmethod
    def from_bytes(cls, data: bytes, media_type: str, filename: str | None = None) -> FileContent:
        """Create from raw bytes.

        Args:
            data: Raw file bytes.
            media_type: MIME type of the file (e.g. ``"application/pdf"``).
            filename: Optional original filename.

        Returns:
            A FileContent with base64-encoded data.
        """
        encoded = base64.b64encode(data).decode("ascii")
        return cls(data=encoded, media_type=media_type, filename=filename)


ContentBlock = Annotated[TextContent | ImageContent | FileContent, Discriminator("type")]


class Message(BaseModel):
    """A message in the conversation history.

    Attributes:
        role: The role of the message sender.
        content: Text string, list of content blocks (for multimodal), or None.
        tool_call_id: ID linking a tool result back to its tool call.
        tool_calls: Tool calls requested by the assistant.
    """

    role: Literal["system", "user", "assistant", "tool"] = Field(
        description="The role of the message sender."
    )
    content: str | list[ContentBlock] | None = Field(
        default=None, description="Text string, list of content blocks, or None."
    )
    tool_call_id: str | None = Field(
        default=None, description="ID linking a tool result back to its tool call."
    )
    tool_calls: list[ToolCallData] | None = Field(
        default=None, description="Tool calls requested by the assistant."
    )

    @property
    def text(self) -> str:
        """Extract text content from this message.

        Returns the string directly for string content, concatenates all
        ``TextContent`` blocks for list content, or returns ``""`` for None.
        """
        if self.content is None:
            return ""
        if isinstance(self.content, str):
            return self.content
        return "".join(block.text for block in self.content if isinstance(block, TextContent))

    @property
    def has_images(self) -> bool:
        """Whether this message contains image content."""
        if not isinstance(self.content, list):
            return False
        return any(isinstance(block, ImageContent) for block in self.content)

    @property
    def has_files(self) -> bool:
        """Whether this message contains file content."""
        if not isinstance(self.content, list):
            return False
        return any(isinstance(block, FileContent) for block in self.content)


class RunMetadata(BaseModel):
    """Metadata about an agent run.

    Attributes:
        run_id: Unique identifier for this run.
        total_tokens: Total tokens consumed (prompt + completion).
        prompt_tokens: Tokens used in prompts sent to the LLM.
        completion_tokens: Tokens generated by the LLM.
        estimated_cost: Estimated cost in USD based on model pricing.
        duration_ms: Wall-clock duration of the run in milliseconds.
        tool_calls_count: Number of tool calls made during the run.
        iterations: Number of LLM call rounds in this run.
    """

    run_id: UUID = Field(description="Unique identifier for this run.")
    total_tokens: int = Field(default=0, description="Total tokens consumed (prompt + completion).")
    prompt_tokens: int = Field(default=0, description="Tokens used in prompts sent to the LLM.")
    completion_tokens: int = Field(default=0, description="Tokens generated by the LLM.")
    estimated_cost: float = Field(
        default=0.0, description="Estimated cost in USD based on model pricing."
    )
    duration_ms: float = Field(
        default=0.0, description="Wall-clock duration of the run in milliseconds."
    )
    tool_calls_count: int = Field(
        default=0, description="Number of tool calls made during the run."
    )
    iterations: int = Field(default=0, description="Number of LLM call rounds in this run.")


class ProviderResponse(BaseModel):
    """Response from an LLM provider.

    Attributes:
        content: Text content of the response, or None if only tool calls.
        tool_calls: Tool calls requested by the model, or None.
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        finish_reason: Why the model stopped (e.g. ``"stop"``, ``"tool_calls"``).
    """

    content: str | None = Field(default=None, description="Text content of the response.")
    tool_calls: list[ToolCallData] | None = Field(
        default=None, description="Tool calls requested by the model."
    )
    prompt_tokens: int = Field(default=0, description="Number of tokens in the prompt.")
    completion_tokens: int = Field(default=0, description="Number of tokens in the completion.")
    finish_reason: str | None = Field(default=None, description="Why the model stopped generating.")


class StreamChunk(BaseModel):
    """A chunk from a streaming LLM response.

    Used for token-by-token streaming in chat UIs.
    """

    content: str = Field(default="", description="Token(s) in this chunk.")
    tool_calls: list[ToolCallData] | None = Field(
        default=None, description="Partial or complete tool calls accumulated so far."
    )
    finish_reason: str | None = Field(
        default=None, description="Set on the final chunk to indicate stop reason."
    )
    is_final: bool = Field(default=False, description="True for the last chunk in the stream.")


class LogEntry(BaseModel):
    """A single entry in the agent execution trace.

    Every significant operation in an agent run produces a LogEntry,
    providing complete observability into agent behavior.
    """

    run_id: UUID = Field(description="ID of the agent run that produced this entry.")
    parent_run_id: UUID | None = Field(
        default=None, description="Parent run ID for multi-agent trace correlation."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this entry was created."
    )
    type: LogType = Field(description="Category of event this entry represents.")
    iteration: int | None = Field(
        default=None, description="Which LLM call round this belongs to (0-indexed)."
    )
    data: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific payload (e.g. tool name, output text)."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (e.g. cost, duration)."
    )

    def model_dump_json_pretty(self) -> str:
        """Return pretty-printed JSON representation.

        Returns:
            JSON string with 2-space indentation.
        """
        return self.model_dump_json(indent=2)


DetailT = TypeVar("DetailT")


class RunResult(BaseModel, Generic[DetailT]):
    """Result of a run (agent or orchestrator).

    Contains the final output, complete execution trace, metadata
    including token usage and cost estimates, and an optional
    pattern-specific detail payload.

    The generic type parameter ``DetailT`` indicates the type of
    the ``detail`` field. For plain agent runs this is typically
    ``None``; orchestrators populate it with pattern-specific
    dataclasses (e.g. ``OrchestrationDetail``, ``SwarmDetail``,
    ``GraphDetail``).
    """

    output: str = Field(description="The final text response.")
    trace: list[LogEntry] = Field(
        default_factory=list, description="Complete execution trace of log entries."
    )
    metadata: RunMetadata = Field(description="Token usage, cost, and timing metadata.")
    detail: DetailT | None = Field(
        default=None,
        description="Pattern-specific detail data (e.g. orchestration steps, "
        "handoff chain, graph execution path).",
    )
    rule_match: Any | None = Field(
        default=None,
        description="RuleMatch if handled by an automation rule (no LLM call). "
        "Typed as Any to avoid circular import with rules module.",
    )
    context: Any | None = Field(
        default=None,
        description="RunContext from the run. Typed as Any to avoid circular import. "
        "Not serialized by Pydantic.",
    )

    @property
    def tool_calls(self) -> list[LogEntry]:
        """Get all tool call entries from the trace."""
        return [entry for entry in self.trace if entry.type == LogType.TOOL_CALL]

    @property
    def errors(self) -> list[LogEntry]:
        """Get all error entries from the trace."""
        return [entry for entry in self.trace if entry.type == LogType.ERROR]

    @property
    def handled_by_rule(self) -> bool:
        """Whether this result was handled by an automation rule (no LLM call)."""
        return self.rule_match is not None


@dataclass
class StreamEvent:
    """A single event in an execution stream.

    Used by ``Orchestrator.stream()`` to emit structured events during
    execution. The ``type`` field discriminates the event kind, and
    ``data`` carries the event-specific payload.

    Common event types:
        - ``"token"`` — LLM token chunk (``{"token": "Hello"}``)
        - ``"tool_call"`` — tool invocation (``{"tool": "...", "args": {...}}``)
        - ``"tool_result"`` — tool result (``{"tool": "...", "result": "..."}``)
        - ``"node_start"`` / ``"node_complete"`` — graph node boundaries
        - ``"agent_start"`` / ``"agent_complete"`` — swarm agent boundaries
        - ``"stage_start"`` / ``"stage_complete"`` — pipeline stage boundaries
        - ``"handoff"`` — swarm agent handoff
        - ``"fan_out"`` / ``"fan_in"`` — parallel execution boundaries
        - ``"complete"`` — final result with output and metadata
        - ``"interrupted"`` — execution paused for human input
        - ``"error"`` — execution failed
    """

    type: str
    data: dict[str, Any] = field(default_factory=dict)
