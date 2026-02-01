"""Logging and cost tracking components for Tantra.

Provides logging, tracing, and cost tracking capabilities.
Every agent operation is fully observable through structured LogEntry objects.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, TextIO
from uuid import UUID, uuid4

from ..types import LogEntry, LogType, RunMetadata


class CostTracker:
    """Tracks token usage and estimates costs for an agent run.

    Supports different pricing models for different providers and models.
    """

    # Default pricing per 1K tokens (as of early 2026)
    DEFAULT_PRICING: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, model: str | None = None):
        """Initialize cost tracker.

        Args:
            model: Model name used to look up default pricing.
        """
        self.model = model
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._custom_pricing: dict[str, float] | None = None

    def set_pricing(self, input_per_1k: float, output_per_1k: float) -> None:
        """Set custom pricing for this tracker.

        Args:
            input_per_1k: Cost per 1K input tokens in USD.
            output_per_1k: Cost per 1K output tokens in USD.
        """
        self._custom_pricing = {"input": input_per_1k, "output": output_per_1k}

    def add_tokens(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage.

        Args:
            prompt_tokens: Number of prompt tokens to add.
            completion_tokens: Number of completion tokens to add.
        """
        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens

    @property
    def prompt_tokens(self) -> int:
        """Total prompt tokens used."""
        return self._prompt_tokens

    @property
    def completion_tokens(self) -> int:
        """Total completion tokens used."""
        return self._completion_tokens

    @property
    def total_tokens(self) -> int:
        """Total tokens used (prompt + completion)."""
        return self._prompt_tokens + self._completion_tokens

    @property
    def estimated_cost(self) -> float:
        """Estimated cost in USD."""
        pricing = self._get_pricing()
        input_cost = (self._prompt_tokens / 1000) * pricing["input"]
        output_cost = (self._completion_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    def _get_pricing(self) -> dict[str, float]:
        """Get pricing for the current model.

        Returns:
            Dict with 'input' and 'output' cost per 1K tokens.
        """
        if self._custom_pricing:
            return self._custom_pricing

        if self.model and self.model in self.DEFAULT_PRICING:
            return self.DEFAULT_PRICING[self.model]

        # Default to GPT-4o pricing if unknown
        return self.DEFAULT_PRICING["gpt-4o"]

    def to_metadata(self) -> dict[str, Any]:
        """Export as metadata dict.

        Returns:
            Dict with prompt_tokens, completion_tokens, total_tokens, and estimated_cost.
        """
        return {
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
        }


class Logger:
    """Collects and manages LogEntry objects for an agent run.

    Provides both collection of logs and optional real-time output
    to various sinks (console, file, custom callbacks).
    """

    def __init__(
        self,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        sink: TextIO | None = None,
        callback: Callable[[LogEntry], None] | None = None,
        pretty: bool = False,
    ):
        """Initialize the logger.

        Args:
            run_id: Unique identifier for this run. Auto-generated if not provided.
            parent_run_id: Optional parent run ID for multi-agent trace correlation.
            sink: Optional TextIO to write logs to (e.g., sys.stdout, file).
            callback: Optional callback function called for each log entry.
            pretty: If True, output pretty-printed JSON to sink.
        """
        self.run_id = run_id or uuid4()
        self.parent_run_id = parent_run_id
        self._entries: list[LogEntry] = []
        self._sink = sink
        self._callback = callback
        self._pretty = pretty
        self._start_time: datetime | None = None
        self._current_iteration: int = 0

    def log(
        self,
        log_type: LogType,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        iteration: int | None = None,
    ) -> LogEntry:
        """Create and record a log entry.

        Args:
            log_type: The type of event being logged.
            data: Event-specific data payload.
            metadata: Additional metadata (tokens, cost, latency, etc.).
            iteration: Optional iteration number (uses current if not provided).

        Returns:
            The created LogEntry.
        """
        entry = LogEntry(
            run_id=self.run_id,
            parent_run_id=self.parent_run_id,
            timestamp=datetime.now(UTC),
            type=log_type,
            iteration=iteration if iteration is not None else self._current_iteration,
            data=data or {},
            metadata=metadata or {},
        )

        self._entries.append(entry)

        # Output to sink if configured
        if self._sink:
            if self._pretty:
                self._sink.write(entry.model_dump_json_pretty() + "\n")
            else:
                self._sink.write(entry.model_dump_json() + "\n")
            self._sink.flush()

        # Call callback if configured
        if self._callback:
            self._callback(entry)

        return entry

    def log_prompt(self, messages: list[dict[str, Any]]) -> LogEntry:
        """Log a prompt being sent to the LLM.

        Args:
            messages: List of message dicts being sent.

        Returns:
            The created LogEntry.
        """
        return self.log(LogType.PROMPT, data={"messages": messages})

    def log_llm_response(
        self,
        content: str | None,
        tool_calls: list[dict[str, Any]] | None,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float | None = None,
    ) -> LogEntry:
        """Log an LLM response.

        Args:
            content: Text content of the response.
            tool_calls: Tool calls requested by the LLM.
            prompt_tokens: Prompt tokens consumed.
            completion_tokens: Completion tokens consumed.
            duration_ms: LLM call duration in milliseconds.

        Returns:
            The created LogEntry.
        """
        metadata = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        if duration_ms is not None:
            metadata["duration_ms"] = duration_ms
        return self.log(
            LogType.LLM_RESPONSE,
            data={"content": content, "tool_calls": tool_calls},
            metadata=metadata,
        )

    def log_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> LogEntry:
        """Log a tool being called.

        Args:
            tool_name: Name of the tool.
            arguments: Arguments passed to the tool.

        Returns:
            The created LogEntry.
        """
        return self.log(
            LogType.TOOL_CALL,
            data={"tool_name": tool_name, "arguments": arguments},
        )

    def log_tool_result(
        self, tool_name: str, result: Any, duration_ms: float | None = None
    ) -> LogEntry:
        """Log a tool result.

        Args:
            tool_name: Name of the tool.
            result: The tool's return value.
            duration_ms: Tool execution duration in milliseconds.

        Returns:
            The created LogEntry.
        """
        metadata = {}
        if duration_ms is not None:
            metadata["duration_ms"] = duration_ms
        return self.log(
            LogType.TOOL_RESULT,
            data={"tool_name": tool_name, "result": result},
            metadata=metadata,
        )

    def log_final_response(self, output: str) -> LogEntry:
        """Log the final agent response.

        Args:
            output: The final output text.

        Returns:
            The created LogEntry.
        """
        return self.log(LogType.FINAL_RESPONSE, data={"output": output})

    def log_error(self, error: Exception, context: str | None = None) -> LogEntry:
        """Log an error.

        Args:
            error: The exception that occurred.
            context: Optional context about where the error happened.

        Returns:
            The created LogEntry.
        """
        return self.log(
            LogType.ERROR,
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
            },
        )

    @property
    def entries(self) -> list[LogEntry]:
        """Get all log entries."""
        return self._entries.copy()

    def clear(self) -> None:
        """Clear all log entries."""
        self._entries.clear()

    def start_run(self) -> None:
        """Mark the start of a run (for duration tracking)."""
        self._start_time = datetime.now(UTC)

    def set_iteration(self, iteration: int) -> None:
        """Set the current iteration number for subsequent log entries.

        Args:
            iteration: The iteration number to use.
        """
        self._current_iteration = iteration

    def get_duration_ms(self) -> float:
        """Get duration since start_run() was called.

        Returns:
            Duration in milliseconds, or 0.0 if start_run() was not called.
        """
        if self._start_time is None:
            return 0.0
        delta = datetime.now(UTC) - self._start_time
        return delta.total_seconds() * 1000


@contextmanager
def console_logger(run_id: UUID | None = None, pretty: bool = True) -> Iterator[Logger]:
    """Context manager for logging to console.

    Examples:
        ```python
        with console_logger() as logger:
            # logger.log(...) outputs to stdout
        ```
    """
    logger = Logger(run_id=run_id, sink=sys.stdout, pretty=pretty)
    yield logger


def create_run_metadata(
    run_id: UUID,
    cost_tracker: CostTracker,
    duration_ms: float,
    tool_calls_count: int,
    iterations: int,
) -> RunMetadata:
    """Create RunMetadata from tracking data.

    Args:
        run_id: The run's unique identifier.
        cost_tracker: CostTracker with accumulated token data.
        duration_ms: Total run duration in milliseconds.
        tool_calls_count: Number of tool calls made.
        iterations: Number of LLM iterations.

    Returns:
        A populated RunMetadata instance.
    """
    return RunMetadata(
        run_id=run_id,
        total_tokens=cost_tracker.total_tokens,
        prompt_tokens=cost_tracker.prompt_tokens,
        completion_tokens=cost_tracker.completion_tokens,
        estimated_cost=cost_tracker.estimated_cost,
        duration_ms=duration_ms,
        tool_calls_count=tool_calls_count,
        iterations=iterations,
    )
