"""Conversation memory implementations for Tantra.

Provides in-memory conversation history storage.
"""

from __future__ import annotations

from ..types import Message
from .base import Memory


class ConversationMemory(Memory):
    """Simple in-memory conversation history.

    Stores messages in a list with optional maximum size.
    When the limit is reached, oldest messages are removed.

    Examples:
        ```python
        memory = ConversationMemory(max_messages=100)
        memory.add_user_message("Hello!")
        memory.add_assistant_message("Hi there!")
        messages = memory.get_messages()
        ```
    """

    def __init__(self, max_messages: int | None = None):
        """Initialize conversation memory.

        Args:
            max_messages: Optional limit on number of messages to keep.
                         When exceeded, oldest messages are removed.
                         None means unlimited.
        """
        self._messages: list[Message] = []
        self._max_messages = max_messages

    def add_message(self, message: Message) -> None:
        """Add a message to memory.

        If max_messages is set and would be exceeded, the oldest
        non-system message is removed.

        Args:
            message: The message to store.
        """
        self._messages.append(message)

        # Trim if over limit
        if self._max_messages and len(self._messages) > self._max_messages:
            # Keep system messages, remove oldest non-system
            self._trim_messages()

    def _trim_messages(self) -> None:
        """Remove oldest messages to stay under limit.

        System messages are preserved for as long as possible. The method
        iterates from the oldest message forward and removes the first
        non-system message it finds. If all messages are system messages,
        the oldest system message is removed as a last resort.
        """
        while self._max_messages and len(self._messages) > self._max_messages:
            # Find first non-system message to remove
            for i, msg in enumerate(self._messages):
                if msg.role != "system":
                    self._messages.pop(i)
                    break
            else:
                # All messages are system messages, just pop the oldest
                self._messages.pop(0)

    def get_messages(self) -> list[Message]:
        """Get all messages in memory.

        Returns:
            A copy of the message list in chronological order.
        """
        return self._messages.copy()

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()

    @property
    def message_count(self) -> int:
        """Number of messages in memory.

        Returns:
            Total count of stored messages, including system messages.
        """
        return len(self._messages)

    def get_last_n(self, n: int) -> list[Message]:
        """Get the last n messages.

        Args:
            n: Number of messages to retrieve.

        Returns:
            Last n messages (or all if fewer exist).
        """
        return self._messages[-n:] if n < len(self._messages) else self._messages.copy()


class WindowedMemory(Memory):
    """Memory that keeps a sliding window of recent messages.

    Unlike ConversationMemory which keeps max_messages total,
    this keeps a system message plus the last N user/assistant exchanges.

    Examples:
        ```python
        memory = WindowedMemory(window_size=5, system_message="You are helpful.")
        memory.add_user_message("Hello!")
        memory.add_assistant_message("Hi there!")
        messages = memory.get_messages()
        # [Message(role="system", ...), Message(role="user", ...), ...]
        ```
    """

    def __init__(self, window_size: int = 10, system_message: str | None = None):
        """Initialize windowed memory.

        Args:
            window_size: Number of recent messages to keep (excluding system).
            system_message: Optional system message to always include first.
        """
        self._window_size = window_size
        self._system_message = system_message
        self._messages: list[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to memory.

        System messages are intercepted and stored separately rather than
        being appended to the sliding window. Adding a system message
        updates (or sets) the persistent system prompt without consuming
        a window slot.

        Args:
            message: The message to store.
        """
        # Don't add to list if it's updating the system message
        if message.role == "system":
            self._system_message = message.text
            return

        self._messages.append(message)

        # Keep only the last window_size messages
        if len(self._messages) > self._window_size:
            self._messages = self._messages[-self._window_size :]

    def get_messages(self) -> list[Message]:
        """Get messages with system message first if present.

        Returns:
            List of messages with the system message (if set) prepended,
            followed by the most recent windowed messages.
        """
        messages = []
        if self._system_message:
            messages.append(Message(role="system", content=self._system_message))
        messages.extend(self._messages)
        return messages

    def clear(self) -> None:
        """Clear all messages (keeps system message)."""
        self._messages.clear()

    def clear_all(self) -> None:
        """Clear all messages including system message."""
        self._messages.clear()
        self._system_message = None

    @property
    def window_size(self) -> int:
        """Current window size setting.

        Returns:
            Maximum number of non-system messages kept in the window.
        """
        return self._window_size
