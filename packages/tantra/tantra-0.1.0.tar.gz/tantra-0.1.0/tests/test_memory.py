"""Tests for memory implementations."""

from tantra import ConversationMemory, Memory, Message, WindowedMemory


class TestConversationMemory:
    """Tests for ConversationMemory."""

    def test_empty_memory(self):
        """New memory is empty."""
        memory = ConversationMemory()
        assert len(memory.get_messages()) == 0

    def test_add_message(self):
        """Add message to memory."""
        memory = ConversationMemory()
        msg = Message(role="user", content="Hello")

        memory.add_message(msg)

        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hello"

    def test_add_multiple_messages(self):
        """Add multiple messages preserves order."""
        memory = ConversationMemory()

        memory.add_message(Message(role="user", content="First"))
        memory.add_message(Message(role="assistant", content="Second"))
        memory.add_message(Message(role="user", content="Third"))

        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"

    def test_clear_memory(self):
        """Clear removes all messages."""
        memory = ConversationMemory()

        memory.add_message(Message(role="user", content="Hello"))
        memory.add_message(Message(role="assistant", content="Hi"))

        memory.clear()

        assert len(memory.get_messages()) == 0

    def test_max_messages(self):
        """Max messages limit works."""
        memory = ConversationMemory(max_messages=3)

        for i in range(5):
            memory.add_message(Message(role="user", content=f"Message {i}"))

        messages = memory.get_messages()
        assert len(messages) == 3
        # Should keep most recent
        assert messages[0].content == "Message 2"
        assert messages[1].content == "Message 3"
        assert messages[2].content == "Message 4"

    def test_returns_copy(self):
        """get_messages returns a copy, not the original list."""
        memory = ConversationMemory()
        memory.add_message(Message(role="user", content="Hello"))

        messages1 = memory.get_messages()
        messages2 = memory.get_messages()

        assert messages1 is not messages2


class TestWindowedMemory:
    """Tests for WindowedMemory."""

    def test_window_size(self):
        """WindowedMemory respects window size."""
        memory = WindowedMemory(window_size=3)

        for i in range(10):
            memory.add_message(Message(role="user", content=f"Message {i}"))

        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[0].content == "Message 7"
        assert messages[1].content == "Message 8"
        assert messages[2].content == "Message 9"

    def test_under_window_size(self):
        """Messages under window size are all kept."""
        memory = WindowedMemory(window_size=10)

        memory.add_message(Message(role="user", content="One"))
        memory.add_message(Message(role="assistant", content="Two"))

        messages = memory.get_messages()
        assert len(messages) == 2

    def test_clear(self):
        """Clear removes all messages."""
        memory = WindowedMemory(window_size=5)

        memory.add_message(Message(role="user", content="Hello"))
        memory.clear()

        assert len(memory.get_messages()) == 0


class TestMemoryABC:
    """Tests for Memory abstract base class."""

    def test_memory_interface(self):
        """Custom memory can implement Memory ABC."""

        class CustomMemory(Memory):
            def __init__(self):
                self._messages = []

            def add_message(self, message):
                self._messages.append(message)

            def get_messages(self):
                return self._messages.copy()

            def clear(self):
                self._messages.clear()

        memory = CustomMemory()
        memory.add_message(Message(role="user", content="Test"))
        assert len(memory.get_messages()) == 1


class TestMessageModel:
    """Tests for Message model."""

    def test_basic_message(self):
        """Create basic message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_call_id is None
        assert msg.tool_calls is None

    def test_tool_message(self):
        """Create tool response message."""
        msg = Message(role="tool", content="Result", tool_call_id="call-123")
        assert msg.role == "tool"
        assert msg.tool_call_id == "call-123"

    def test_assistant_with_tool_calls(self):
        """Create assistant message with tool calls."""
        from tantra.types import ToolCallData

        tool_calls = [ToolCallData(id="call-1", name="get_weather", arguments={"city": "NYC"})]
        msg = Message(role="assistant", content=None, tool_calls=tool_calls)

        assert msg.role == "assistant"
        assert msg.content is None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "get_weather"

    def test_message_serialization(self):
        """Message serializes to dict."""
        msg = Message(role="user", content="Hello")
        data = msg.model_dump()

        assert data["role"] == "user"
        assert data["content"] == "Hello"
