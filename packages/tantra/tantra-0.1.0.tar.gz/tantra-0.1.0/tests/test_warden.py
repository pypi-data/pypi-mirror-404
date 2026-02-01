"""Tests for the Warden Pattern."""

import pytest

from tantra import (
    Interrupt,
    InterruptHandler,
    Warden,
    WardenPreview,
    WardenTool,
    WardenToolSet,
    warden_tool,
)


class MockWardenHandler(InterruptHandler):
    """Mock handler that records notify() calls."""

    def __init__(self):
        self.received_interrupts: list[Interrupt] = []

    async def notify(self, interrupt: Interrupt) -> None:
        self.received_interrupts.append(interrupt)


class TestWardenTool:
    """Tests for warden_tool decorator."""

    def test_create_warden_tool(self):
        """Create a basic warden tool."""

        @warden_tool
        def my_tool(arg: str) -> str:
            """My tool description."""
            return f"Result: {arg}"

        assert isinstance(my_tool, WardenTool)
        assert my_tool.name == "my_tool"
        assert my_tool._is_warden is True

    def test_warden_tool_with_custom_name(self):
        """Warden tool with custom name."""

        @warden_tool(name="custom_name")
        def my_tool() -> str:
            return "done"

        assert my_tool.name == "custom_name"

    def test_warden_tool_without_preview(self):
        """Warden tool without preview function."""

        @warden_tool
        def my_tool() -> str:
            return "done"

        assert my_tool.has_preview is False

    def test_warden_tool_with_preview(self):
        """Warden tool with preview function."""

        @warden_tool
        def my_tool(path: str) -> str:
            return f"Processed {path}"

        @my_tool.preview
        def preview_my_tool(path: str) -> WardenPreview:
            return WardenPreview(
                tool_name="my_tool",
                arguments={"path": path},
                preview_result=f"Will process: {path}",
                description="Process the path",
            )

        assert my_tool.has_preview is True


class TestWardenPreview:
    """Tests for WardenPreview."""

    def test_create_preview(self):
        """Create a preview."""
        preview = WardenPreview(
            tool_name="delete_file",
            arguments={"path": "/tmp/test.txt"},
            preview_result="File size: 1024 bytes",
            description="Delete file",
            risks=["Data loss"],
            reversible=False,
        )

        assert preview.tool_name == "delete_file"
        assert preview.arguments == {"path": "/tmp/test.txt"}
        assert preview.reversible is False
        assert "Data loss" in preview.risks

    def test_preview_defaults(self):
        """Preview has sensible defaults."""
        preview = WardenPreview(
            tool_name="my_tool",
            arguments={},
            preview_result="Result",
        )

        assert preview.reversible is True
        assert preview.risks == []
        assert preview.description == ""


class TestWardenToolExecution:
    """Tests for warden tool preview and execution."""

    @pytest.mark.asyncio
    async def test_get_preview_with_function(self):
        """Get preview from tool with preview function."""

        @warden_tool
        def delete_file(path: str) -> str:
            return f"Deleted {path}"

        @delete_file.preview
        def preview_delete(path: str) -> WardenPreview:
            return WardenPreview(
                tool_name="delete_file",
                arguments={"path": path},
                preview_result=f"Will delete: {path}",
                description="Permanent deletion",
                risks=["Cannot undo"],
                reversible=False,
            )

        preview = await delete_file.get_preview(path="/tmp/test.txt")

        assert preview.tool_name == "delete_file"
        assert preview.preview_result == "Will delete: /tmp/test.txt"
        assert preview.reversible is False

    @pytest.mark.asyncio
    async def test_get_preview_without_function(self):
        """Get default preview when no preview function."""

        @warden_tool
        def my_tool(x: int) -> int:
            return x * 2

        preview = await my_tool.get_preview(x=5)

        assert preview.tool_name == "my_tool"
        assert preview.arguments == {"x": 5}
        assert "(No preview available)" in preview.preview_result

    @pytest.mark.asyncio
    async def test_async_preview_function(self):
        """Preview function can be async."""

        @warden_tool
        def my_tool(data: str) -> str:
            return data

        @my_tool.preview
        async def async_preview(data: str) -> WardenPreview:
            # Simulate async operation
            return WardenPreview(
                tool_name="my_tool",
                arguments={"data": data},
                preview_result=f"Async preview: {data}",
            )

        preview = await my_tool.get_preview(data="test")
        assert "Async preview" in preview.preview_result


class TestWarden:
    """Tests for Warden class."""

    @pytest.mark.asyncio
    async def test_warden_review_not_auto_approved(self):
        """Warden review returns (False, preview) when not auto-approved."""
        handler = MockWardenHandler()
        warden = Warden(handler=handler)

        @warden_tool
        def dangerous_op() -> str:
            return "done"

        @dangerous_op.preview
        def preview_dangerous() -> WardenPreview:
            return WardenPreview(
                tool_name="dangerous_op",
                arguments={},
                preview_result="Will do something dangerous",
            )

        auto_approved, preview = await warden.review(dangerous_op, {})

        assert auto_approved is False
        assert isinstance(preview, WardenPreview)
        assert preview.tool_name == "dangerous_op"
        # Handler is NOT called by review() — engine calls notify()
        assert len(handler.received_interrupts) == 0

    @pytest.mark.asyncio
    async def test_warden_auto_approve_reversible(self):
        """Warden auto-approves reversible actions when configured."""
        handler = MockWardenHandler()
        warden = Warden(handler=handler, auto_approve_reversible=True)

        @warden_tool
        def safe_op() -> str:
            return "done"

        @safe_op.preview
        def preview_safe() -> WardenPreview:
            return WardenPreview(
                tool_name="safe_op",
                arguments={},
                preview_result="Safe operation",
                reversible=True,  # Reversible
            )

        auto_approved, preview = await warden.review(safe_op, {})

        assert auto_approved is True
        assert isinstance(preview, WardenPreview)
        # Handler should NOT be called for auto-approved
        assert len(handler.received_interrupts) == 0

    @pytest.mark.asyncio
    async def test_warden_no_auto_approve_irreversible(self):
        """Warden does not auto-approve irreversible actions."""
        handler = MockWardenHandler()
        warden = Warden(handler=handler, auto_approve_reversible=True)

        @warden_tool
        def dangerous_op() -> str:
            return "done"

        @dangerous_op.preview
        def preview_dangerous() -> WardenPreview:
            return WardenPreview(
                tool_name="dangerous_op",
                arguments={},
                preview_result="Dangerous",
                reversible=False,  # Not reversible
            )

        auto_approved, preview = await warden.review(dangerous_op, {})

        assert auto_approved is False
        assert isinstance(preview, WardenPreview)

    def test_warden_prompt_includes_risks(self):
        """Warden prompt includes risk information."""
        warden = Warden(handler=MockWardenHandler())

        preview = WardenPreview(
            tool_name="delete_all",
            arguments={},
            preview_result="Will delete everything",
            description="Delete all data",
            risks=["Total data loss", "Cannot be undone"],
            reversible=False,
        )

        prompt = warden._build_prompt(preview)

        assert "WARDEN REVIEW" in prompt
        assert "delete_all" in prompt
        assert "Total data loss" in prompt
        assert "Cannot be undone" in prompt
        assert "Reversible: No" in prompt


class TestWardenToolSet:
    """Tests for WardenToolSet."""

    def test_identify_warden_tools(self):
        """WardenToolSet identifies warden tools."""

        @warden_tool
        def warden_op() -> str:
            return "warden"

        from tantra import tool

        @tool
        def regular_op() -> str:
            return "regular"

        toolset = WardenToolSet([warden_op, regular_op])

        assert toolset.is_warden_tool("warden_op") is True
        assert toolset.is_warden_tool("regular_op") is False

    @pytest.mark.asyncio
    async def test_preview_warden_tool(self):
        """Get preview for warden tool in toolset."""

        @warden_tool
        def my_tool(x: int) -> int:
            return x

        @my_tool.preview
        def preview_tool(x: int) -> WardenPreview:
            return WardenPreview(
                tool_name="my_tool",
                arguments={"x": x},
                preview_result=f"Will return {x}",
            )

        toolset = WardenToolSet([my_tool])
        preview = await toolset.preview("my_tool", {"x": 42})

        assert preview is not None
        assert "42" in preview.preview_result

    @pytest.mark.asyncio
    async def test_preview_regular_tool_returns_none(self):
        """Preview returns None for regular tools."""
        from tantra import tool

        @tool
        def regular_tool() -> str:
            return "regular"

        toolset = WardenToolSet([regular_tool])
        preview = await toolset.preview("regular_tool", {})

        assert preview is None

    @pytest.mark.asyncio
    async def test_execute_with_review_auto_approved(self):
        """Execute with review when auto-approved (reversible)."""
        handler = MockWardenHandler()
        warden = Warden(handler=handler, auto_approve_reversible=True)

        @warden_tool
        def my_tool() -> str:
            return "executed"

        @my_tool.preview
        def preview_my_tool() -> WardenPreview:
            return WardenPreview(
                tool_name="my_tool",
                arguments={},
                preview_result="Will execute",
                reversible=True,
            )

        toolset = WardenToolSet([my_tool], warden=warden)
        result, approved = await toolset.execute_with_review("my_tool", {})

        assert approved is True
        assert result == "executed"

    @pytest.mark.asyncio
    async def test_execute_with_review_not_auto_approved(self):
        """Execute with review when not auto-approved returns (preview, False)."""
        handler = MockWardenHandler()
        warden = Warden(handler=handler, auto_approve_reversible=True)

        @warden_tool
        def my_tool() -> str:
            return "should not execute"

        @my_tool.preview
        def preview_my_tool() -> WardenPreview:
            return WardenPreview(
                tool_name="my_tool",
                arguments={},
                preview_result="Would execute",
                reversible=False,
            )

        toolset = WardenToolSet([my_tool], warden=warden)
        result, approved = await toolset.execute_with_review("my_tool", {})

        assert approved is False
        assert isinstance(result, WardenPreview)
