"""Base classes for memory in Tantra.

Provides the Memory interface for conversation history.
Implement this to create custom memory backends (Redis, PostgreSQL, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import Message


class Memory(ABC):
    """Abstract base class for agent memory.

    Memory stores and retrieves conversation history and context.
    Implement this class to create custom memory backends.

    Examples:
        ```python
        class RedisMemory(Memory):
            def __init__(self, redis_client):
                self._redis = redis_client

            def add_message(self, message: Message) -> None:
                self._redis.rpush("messages", message.model_dump_json())

            def get_messages(self) -> list[Message]:
                # ... retrieve from Redis
                pass

            def clear(self) -> None:
                self._redis.delete("messages")
        ```
    """

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: The message to store.

        Note:
            Subclasses may raise backend-specific errors (e.g. connection
            errors for Redis or database backends).
        """
        pass

    @abstractmethod
    def get_messages(self) -> list[Message]:
        """Get all messages from memory.

        Returns:
            List of messages in chronological order.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all messages from memory.

        Note:
            Subclasses may choose to preserve system messages. See
            ``WindowedMemory.clear()`` for an example.
        """
        pass

    def add_user_message(self, content: str) -> None:
        """Convenience method to add a user message.

        Delegates to ``add_message`` with ``role="user"``.

        Args:
            content: The message content.
        """
        self.add_message(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        """Convenience method to add an assistant message.

        Delegates to ``add_message`` with ``role="assistant"``.

        Args:
            content: The message content.
        """
        self.add_message(Message(role="assistant", content=content))

    def add_system_message(self, content: str) -> None:
        """Convenience method to add a system message.

        Delegates to ``add_message`` with ``role="system"``.

        Args:
            content: The message content.
        """
        self.add_message(Message(role="system", content=content))
