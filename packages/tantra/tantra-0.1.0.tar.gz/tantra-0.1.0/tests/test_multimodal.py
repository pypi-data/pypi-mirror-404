"""Tests for multimodal message support."""

import base64
import json

import pytest

from tantra import Agent, FileContent, ImageContent, Message, TextContent


@pytest.fixture(autouse=True)
def mock_api_keys(monkeypatch):
    """Set dummy API keys for provider instantiation."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")


# ---------------------------------------------------------------------------
# Content block types
# ---------------------------------------------------------------------------


class TestTextContent:
    def test_creation(self):
        tc = TextContent(text="hello")
        assert tc.type == "text"
        assert tc.text == "hello"

    def test_type_literal(self):
        tc = TextContent(text="x")
        assert tc.model_dump()["type"] == "text"


class TestImageContent:
    def test_from_bytes(self):
        raw = b"\x89PNG\r\n"
        img = ImageContent.from_bytes(raw, media_type="image/png")
        assert img.type == "image"
        assert img.data == base64.b64encode(raw).decode("ascii")
        assert img.media_type == "image/png"
        assert img.url is None

    def test_from_url(self):
        img = ImageContent.from_url("https://example.com/img.jpg", media_type="image/jpeg")
        assert img.url == "https://example.com/img.jpg"
        assert img.data is None
        assert img.media_type == "image/jpeg"

    def test_from_url_with_detail(self):
        img = ImageContent.from_url("https://x.com/i.png", detail="low")
        assert img.detail == "low"

    def test_from_file(self, tmp_path):
        # Create a fake PNG file
        png = tmp_path / "test.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        img = ImageContent.from_file(png)
        assert img.media_type == "image/png"
        assert img.data is not None
        # Round-trip: decode should give back original bytes
        assert base64.b64decode(img.data) == png.read_bytes()

    def test_from_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            ImageContent.from_file("/nonexistent/photo.jpg")

    def test_from_file_invalid_type(self, tmp_path):
        txt = tmp_path / "notes.txt"
        txt.write_text("not an image")
        with pytest.raises(ValueError, match="Cannot determine image MIME type"):
            ImageContent.from_file(txt)

    def test_serialization_roundtrip(self):
        img = ImageContent.from_bytes(b"abc", media_type="image/jpeg")
        data = img.model_dump()
        restored = ImageContent(**data)
        assert restored.data == img.data
        assert restored.media_type == img.media_type


class TestFileContent:
    def test_from_bytes(self):
        raw = b"%PDF-1.4 fake content"
        fc = FileContent.from_bytes(raw, media_type="application/pdf", filename="doc.pdf")
        assert fc.type == "file"
        assert fc.data == base64.b64encode(raw).decode("ascii")
        assert fc.media_type == "application/pdf"
        assert fc.filename == "doc.pdf"

    def test_from_bytes_no_filename(self):
        fc = FileContent.from_bytes(b"data", media_type="text/csv")
        assert fc.filename is None

    def test_from_file(self, tmp_path):
        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        fc = FileContent.from_file(pdf)
        assert fc.media_type == "application/pdf"
        assert fc.filename == "report.pdf"
        assert base64.b64decode(fc.data) == pdf.read_bytes()

    def test_from_file_text(self, tmp_path):
        txt = tmp_path / "notes.txt"
        txt.write_text("hello world")
        fc = FileContent.from_file(txt)
        assert fc.media_type == "text/plain"
        assert fc.filename == "notes.txt"

    def test_from_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileContent.from_file("/nonexistent/doc.pdf")

    def test_from_file_unknown_mime(self, tmp_path):
        unknown = tmp_path / "data.xyz123"
        unknown.write_bytes(b"mystery")
        with pytest.raises(ValueError, match="Cannot determine MIME type"):
            FileContent.from_file(unknown)

    def test_serialization_roundtrip(self):
        fc = FileContent.from_bytes(b"content", media_type="application/pdf", filename="f.pdf")
        data = fc.model_dump()
        restored = FileContent(**data)
        assert restored.data == fc.data
        assert restored.media_type == fc.media_type
        assert restored.filename == fc.filename


# ---------------------------------------------------------------------------
# Message with multimodal content
# ---------------------------------------------------------------------------


class TestMessageMultimodal:
    def test_string_content_unchanged(self):
        msg = Message(role="user", content="hello")
        assert msg.content == "hello"
        assert isinstance(msg.content, str)

    def test_content_blocks(self):
        blocks = [
            TextContent(text="What is this?"),
            ImageContent.from_bytes(b"fake", media_type="image/png"),
        ]
        msg = Message(role="user", content=blocks)
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2

    def test_text_property_from_string(self):
        msg = Message(role="user", content="hello")
        assert msg.text == "hello"

    def test_text_property_from_blocks(self):
        blocks = [
            TextContent(text="part1"),
            ImageContent.from_bytes(b"x"),
            TextContent(text="part2"),
        ]
        msg = Message(role="user", content=blocks)
        assert msg.text == "part1part2"

    def test_text_property_from_none(self):
        msg = Message(role="assistant", content=None)
        assert msg.text == ""

    def test_has_images_false_for_string(self):
        msg = Message(role="user", content="no images")
        assert msg.has_images is False

    def test_has_images_false_for_none(self):
        msg = Message(role="assistant")
        assert msg.has_images is False

    def test_has_images_true(self):
        blocks = [
            TextContent(text="look"),
            ImageContent.from_bytes(b"x"),
        ]
        msg = Message(role="user", content=blocks)
        assert msg.has_images is True

    def test_has_images_false_text_only_blocks(self):
        blocks = [TextContent(text="just text")]
        msg = Message(role="user", content=blocks)
        assert msg.has_images is False

    def test_has_files_true(self):
        blocks = [
            TextContent(text="read this"),
            FileContent.from_bytes(b"pdf", media_type="application/pdf"),
        ]
        msg = Message(role="user", content=blocks)
        assert msg.has_files is True
        assert msg.has_images is False

    def test_has_files_false_for_string(self):
        msg = Message(role="user", content="no files")
        assert msg.has_files is False

    def test_file_content_text_property(self):
        blocks = [
            TextContent(text="summarize"),
            FileContent.from_bytes(b"pdf", media_type="application/pdf"),
        ]
        msg = Message(role="user", content=blocks)
        assert msg.text == "summarize"

    def test_serialization_roundtrip(self):
        """Message with content blocks can be serialized and deserialized."""
        blocks = [
            TextContent(text="describe this"),
            ImageContent.from_bytes(b"img", media_type="image/png"),
        ]
        msg = Message(role="user", content=blocks)
        data = msg.model_dump()
        restored = Message(**data)
        assert restored.text == "describe this"
        assert restored.has_images is True
        assert len(restored.content) == 2

    def test_json_serialization_roundtrip(self):
        """Message survives JSON serialization (critical for checkpoint store)."""
        blocks = [
            TextContent(text="check"),
            ImageContent.from_url("https://x.com/a.png"),
        ]
        msg = Message(role="user", content=blocks)
        json_str = msg.model_dump_json()
        data = json.loads(json_str)
        restored = Message(**data)
        assert restored.text == "check"
        assert restored.has_images is True

    def test_json_roundtrip_with_file(self):
        """Message with FileContent survives JSON serialization."""
        blocks = [
            TextContent(text="read"),
            FileContent.from_bytes(b"pdf", media_type="application/pdf", filename="x.pdf"),
        ]
        msg = Message(role="user", content=blocks)
        json_str = msg.model_dump_json()
        data = json.loads(json_str)
        restored = Message(**data)
        assert restored.text == "read"
        assert restored.has_files is True
        assert isinstance(restored.content[1], FileContent)
        assert restored.content[1].filename == "x.pdf"


# ---------------------------------------------------------------------------
# Agent with attachments
# ---------------------------------------------------------------------------


class TestAgentMultimodal:
    @pytest.mark.asyncio
    async def test_run_with_attachments(self, mock_provider):
        agent = Agent(mock_provider, system_prompt="You are helpful.")
        img = ImageContent.from_bytes(b"test-image", media_type="image/png")
        result = await agent.run("What's in this image?", attachments=[img])
        assert result.output == "Hello!"

        # Verify the provider received multimodal content
        call = mock_provider.calls[0]
        user_msg = [m for m in call["messages"] if m.role == "user"][0]
        assert isinstance(user_msg.content, list)
        assert len(user_msg.content) == 2
        assert isinstance(user_msg.content[0], TextContent)
        assert isinstance(user_msg.content[1], ImageContent)

    @pytest.mark.asyncio
    async def test_run_without_attachments_unchanged(self, mock_provider):
        agent = Agent(mock_provider, system_prompt="You are helpful.")
        result = await agent.run("Hello!")
        assert result.output == "Hello!"

        # Verify content is plain string (backward compat)
        call = mock_provider.calls[0]
        user_msg = [m for m in call["messages"] if m.role == "user"][0]
        assert isinstance(user_msg.content, str)
        assert user_msg.content == "Hello!"

    @pytest.mark.asyncio
    async def test_attachments_stored_in_memory(self, mock_provider):
        agent = Agent(mock_provider)
        img = ImageContent.from_bytes(b"x", media_type="image/jpeg")
        await agent.run("describe", attachments=[img])

        # Check that memory contains the multimodal message
        messages = agent.memory.get_messages()
        user_msgs = [m for m in messages if m.role == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0].has_images is True

    @pytest.mark.asyncio
    async def test_multiple_attachments(self, mock_provider):
        agent = Agent(mock_provider)
        imgs = [
            ImageContent.from_bytes(b"img1", media_type="image/png"),
            ImageContent.from_bytes(b"img2", media_type="image/jpeg"),
        ]
        result = await agent.run("Compare these", attachments=imgs)
        assert result.output == "Hello!"

        call = mock_provider.calls[0]
        user_msg = [m for m in call["messages"] if m.role == "user"][0]
        assert len(user_msg.content) == 3  # 1 text + 2 images

    @pytest.mark.asyncio
    async def test_run_with_file_attachment(self, mock_provider):
        agent = Agent(mock_provider)
        fc = FileContent.from_bytes(b"pdf-data", media_type="application/pdf", filename="doc.pdf")
        result = await agent.run("Summarize this document", attachments=[fc])
        assert result.output == "Hello!"

        call = mock_provider.calls[0]
        user_msg = [m for m in call["messages"] if m.role == "user"][0]
        assert isinstance(user_msg.content, list)
        assert len(user_msg.content) == 2
        assert isinstance(user_msg.content[0], TextContent)
        assert isinstance(user_msg.content[1], FileContent)
        assert user_msg.content[1].filename == "doc.pdf"

    @pytest.mark.asyncio
    async def test_run_with_mixed_attachments(self, mock_provider):
        agent = Agent(mock_provider)
        attachments = [
            ImageContent.from_bytes(b"img", media_type="image/png"),
            FileContent.from_bytes(b"pdf", media_type="application/pdf"),
        ]
        result = await agent.run("Analyze these", attachments=attachments)
        assert result.output == "Hello!"

        call = mock_provider.calls[0]
        user_msg = [m for m in call["messages"] if m.role == "user"][0]
        assert len(user_msg.content) == 3  # 1 text + 1 image + 1 file
        assert user_msg.has_images is True
        assert user_msg.has_files is True


# ---------------------------------------------------------------------------
# Engine _build_user_message
# ---------------------------------------------------------------------------


class TestEngineMultimodal:
    def test_build_user_message_no_attachments(self, mock_provider):
        from tantra.engine import ExecutionEngine

        engine = ExecutionEngine(provider=mock_provider)
        msg = engine._build_user_message("hello")
        assert isinstance(msg.content, str)
        assert msg.content == "hello"

    def test_build_user_message_with_attachments(self, mock_provider):
        from tantra.engine import ExecutionEngine

        engine = ExecutionEngine(provider=mock_provider)
        img = ImageContent.from_bytes(b"data", media_type="image/png")
        msg = engine._build_user_message("describe", attachments=[img])
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2
        assert msg.text == "describe"
        assert msg.has_images is True


# ---------------------------------------------------------------------------
# Provider conversion
# ---------------------------------------------------------------------------


class TestOpenAIMultimodal:
    @pytest.fixture
    def provider(self, mock_api_keys):
        from tantra.providers.openai import OpenAIProvider

        return OpenAIProvider("gpt-4o")

    def test_convert_string_content(self, provider):
        msgs = [Message(role="user", content="hi")]
        result = provider._convert_messages(msgs)
        assert result[0]["content"] == "hi"

    def test_convert_content_blocks(self, provider):
        blocks = [
            TextContent(text="look"),
            ImageContent.from_bytes(b"x", media_type="image/png"),
        ]
        msgs = [Message(role="user", content=blocks)]
        result = provider._convert_messages(msgs)
        parts = result[0]["content"]
        assert len(parts) == 2
        assert parts[0] == {"type": "text", "text": "look"}
        assert parts[1]["type"] == "image_url"
        assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")

    def test_convert_image_url(self, provider):
        blocks = [ImageContent.from_url("https://x.com/img.png")]
        msgs = [Message(role="user", content=blocks)]
        result = provider._convert_messages(msgs)
        part = result[0]["content"][0]
        assert part["image_url"]["url"] == "https://x.com/img.png"

    def test_token_count_with_images(self, provider):
        blocks = [
            TextContent(text="hello"),
            ImageContent.from_bytes(b"x"),
        ]
        msgs = [Message(role="user", content=blocks)]
        count = provider.count_tokens(msgs)
        # Should include text tokens + 765 for image (default detail) + overhead
        assert count > 765

    def test_token_count_string_unchanged(self, provider):
        msgs = [Message(role="user", content="hello")]
        count = provider.count_tokens(msgs)
        assert count > 0
        assert count < 100  # Sanity: small text should be small


class TestAnthropicMultimodal:
    @pytest.fixture
    def provider(self, mock_api_keys):
        from tantra.providers.anthropic import AnthropicProvider

        return AnthropicProvider("claude-3-5-sonnet-20241022")

    def test_convert_string_content(self, provider):
        msgs = [Message(role="user", content="hi")]
        system, result = provider._convert_messages(msgs)
        assert result[0]["content"] == "hi"

    def test_convert_content_blocks(self, provider):
        blocks = [
            TextContent(text="describe"),
            ImageContent.from_bytes(b"x", media_type="image/jpeg"),
        ]
        msgs = [Message(role="user", content=blocks)]
        system, result = provider._convert_messages(msgs)
        parts = result[0]["content"]
        assert len(parts) == 2
        assert parts[0] == {"type": "text", "text": "describe"}
        assert parts[1]["type"] == "image"
        assert parts[1]["source"]["type"] == "base64"
        assert parts[1]["source"]["media_type"] == "image/jpeg"

    def test_convert_image_url(self, provider):
        blocks = [ImageContent.from_url("https://x.com/img.png")]
        msgs = [Message(role="user", content=blocks)]
        system, result = provider._convert_messages(msgs)
        part = result[0]["content"][0]
        assert part["type"] == "image"
        assert part["source"]["type"] == "url"
        assert part["source"]["url"] == "https://x.com/img.png"

    def test_system_message_extracts_text(self, provider):
        # System messages should always extract text even if content is blocks
        msgs = [
            Message(role="system", content="Be helpful"),
            Message(role="user", content="hi"),
        ]
        system, result = provider._convert_messages(msgs)
        assert system == "Be helpful"
        assert len(result) == 1

    def test_token_count_with_images(self, provider):
        blocks = [
            TextContent(text="hello"),
            ImageContent.from_bytes(b"x"),
        ]
        msgs = [Message(role="user", content=blocks)]
        count = provider.count_tokens(msgs)
        assert count > 1600  # Image estimate


class TestOllamaMultimodal:
    @pytest.fixture
    def provider(self):
        from tantra.providers.ollama import OllamaProvider

        return OllamaProvider("llava")

    def test_convert_string_content(self, provider):
        msgs = [Message(role="user", content="hi")]
        result = provider._convert_messages(msgs)
        assert result[0]["content"] == "hi"
        assert "images" not in result[0]

    def test_convert_content_blocks(self, provider):
        img_data = b"fake-image"
        blocks = [
            TextContent(text="what is this?"),
            ImageContent.from_bytes(img_data, media_type="image/png"),
        ]
        msgs = [Message(role="user", content=blocks)]
        result = provider._convert_messages(msgs)
        assert result[0]["content"] == "what is this?"
        assert "images" in result[0]
        assert len(result[0]["images"]) == 1
        assert result[0]["images"][0] == base64.b64encode(img_data).decode("ascii")

    def test_url_images_skipped(self, provider):
        # Ollama doesn't support URL images, only base64
        blocks = [
            TextContent(text="look"),
            ImageContent.from_url("https://x.com/i.png"),
        ]
        msgs = [Message(role="user", content=blocks)]
        result = provider._convert_messages(msgs)
        assert result[0]["content"] == "look"
        assert "images" not in result[0]

    def test_token_count_with_images(self, provider):
        blocks = [
            TextContent(text="hello"),
            ImageContent.from_bytes(b"x"),
        ]
        msgs = [Message(role="user", content=blocks)]
        count = provider.count_tokens(msgs)
        assert count > 768  # Image estimate


# ---------------------------------------------------------------------------
# WindowedMemory with multimodal
# ---------------------------------------------------------------------------


class TestWindowedMemoryMultimodal:
    def test_system_message_extracts_text(self):
        from tantra.memory import WindowedMemory

        mem = WindowedMemory(window_size=5)
        # Even if someone constructs a system message with blocks, it extracts text
        blocks = [TextContent(text="Be helpful")]
        mem.add_message(Message(role="system", content=blocks))
        messages = mem.get_messages()
        assert messages[0].role == "system"
        assert messages[0].content == "Be helpful"

    def test_user_message_with_images_stored(self):
        from tantra.memory import WindowedMemory

        mem = WindowedMemory(window_size=5)
        blocks = [
            TextContent(text="look"),
            ImageContent.from_bytes(b"x"),
        ]
        mem.add_message(Message(role="user", content=blocks))
        messages = mem.get_messages()
        assert messages[0].has_images is True
