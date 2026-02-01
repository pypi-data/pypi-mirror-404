"""Base classes for interrupt handling in Tantra.

Provides the InterruptHandler interface that users can extend
to create custom interrupt notification flows (Slack, Discord, custom UI, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Interrupt(BaseModel):
    """An interrupt that pauses execution for human input.

    Contains all context needed for a human to make a decision.

    Attributes:
        id: Unique interrupt identifier.
        run_id: ID of the agent run that triggered this interrupt.
        name: Optional name of the agent.
        prompt: Human-readable prompt describing what input is needed.
        context: Additional context for the decision.
        tool_name: Name of the tool that triggered the interrupt, if any.
        tool_args: Arguments of the triggering tool call, if any.
        created_at: When the interrupt was created.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    run_id: UUID
    name: str | None = None
    prompt: str
    context: dict[str, Any] = {}
    tool_name: str | None = None
    tool_args: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InterruptResponse(BaseModel):
    """Human's response to an interrupt.

    Attributes:
        value: The actual response (True/False, string, dict, etc.).
        proceed: If False, abort the agent run.
        reason: Optional explanation for the decision.
    """

    value: Any = None
    proceed: bool = True
    reason: str | None = None


class InterruptHandler(ABC):
    """Base class for interrupt handlers.

    Implement this to create custom interrupt notification flows
    (Slack, Discord, custom UI, etc.). The handler is notified when
    an interrupt occurs; it does not return a response. Resumption
    is always explicit via ``agent.resume()``.

    Examples:
        ```python
        class SlackInterruptHandler(InterruptHandler):
            async def notify(self, interrupt: Interrupt) -> None:
                # Post to Slack channel for async review
                await self.slack.post(interrupt.prompt)
        ```
    """

    @abstractmethod
    async def notify(self, interrupt: Interrupt) -> None:
        """Notify about an interrupt (fire-and-forget).

        Called before the engine creates a checkpoint and raises
        ``ExecutionInterruptedError``. Use this to send notifications
        (Slack, email, webhook, etc.) so a human can later call
        ``agent.resume()`` with an ``InterruptResponse``.

        Args:
            interrupt: The interrupt to notify about.
        """
        pass


class CallbackInterruptHandler(InterruptHandler):
    """Interrupt handler that calls a custom async function.

    Maximum flexibility for custom implementations.

    Examples:
        ```python
        async def my_handler(interrupt: Interrupt) -> None:
            # Custom notification logic here
            await send_notification(interrupt.prompt)

        handler = CallbackInterruptHandler(my_handler)
        ```
    """

    def __init__(self, callback: Callable[[Interrupt], None]):
        """Initialize with a callback function.

        Args:
            callback: Async function that takes an Interrupt. Return value is ignored.
        """
        self._callback = callback

    async def notify(self, interrupt: Interrupt) -> None:
        """Delegate to the callback function.

        Args:
            interrupt: The interrupt to notify about.
        """
        await self._callback(interrupt)
