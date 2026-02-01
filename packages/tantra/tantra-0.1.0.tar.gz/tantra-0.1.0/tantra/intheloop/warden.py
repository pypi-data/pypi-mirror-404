"""Warden Pattern for Tantra.

Provides sandboxed execution with human review before actions fire.
Tools can provide a preview function that shows what WOULD happen,
allowing humans to review before the actual execution.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..tools import ToolDefinition, ToolSet
from .base import InterruptHandler


@dataclass
class WardenPreview:
    """Preview of what a tool would do.

    Attributes:
        tool_name: Name of the tool being previewed.
        arguments: Arguments that would be passed to the tool.
        preview_result: Result of the dry-run / preview execution.
        description: Human-readable description of the action.
        risks: List of identified risks for this action.
        reversible: Whether the action can be undone.
    """

    tool_name: str
    arguments: dict[str, Any]
    preview_result: Any
    description: str = ""
    risks: list[str] = field(default_factory=list)
    reversible: bool = True


class WardenTool(ToolDefinition):
    """A tool with preview capability for the Warden Pattern.

    Warden tools execute in two phases:
    1. Preview - show what WOULD happen (sandboxed/dry-run)
    2. Execute - actually perform the action (after approval)

    Examples:
        ```python
        @warden_tool
        def delete_file(path: str) -> str:
            '''Delete a file from the filesystem.'''
            os.remove(path)
            return f"Deleted {path}"

        @delete_file.preview
        def preview_delete(path: str) -> WardenPreview:
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            return WardenPreview(
                tool_name="delete_file",
                arguments={"path": path},
                preview_result=f"File: {path} ({size} bytes)",
                description=f"Will permanently delete {path}",
                risks=["Data loss - file cannot be recovered"],
                reversible=False,
            )
        ```
    """

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
        preview_func: Callable | None = None,
    ):
        """Initialize a warden tool.

        Args:
            func: The tool function to execute.
            name: Optional override for the tool name.
            description: Optional override for the tool description.
            preview_func: Optional preview/dry-run function.
        """
        # Initialize without interrupt - warden handles this differently
        super().__init__(func, name=name, description=description, interrupt=None)
        self._preview_func = preview_func
        self._is_warden = True

    @property
    def has_preview(self) -> bool:
        """Whether this tool has a preview function."""
        return self._preview_func is not None

    def preview(self, func: Callable) -> Callable:
        """Decorator to set the preview function.

        Examples:
            ```python
            @my_tool.preview
            def preview_my_tool(arg: str) -> WardenPreview:
                return WardenPreview(...)
            ```
        """
        self._preview_func = func
        return func

    async def get_preview(self, **kwargs: Any) -> WardenPreview:
        """Get preview of what this tool would do.

        Args:
            **kwargs: Tool arguments to preview.

        Returns:
            A WardenPreview describing the action.
        """
        if not self._preview_func:
            # Default preview if none provided
            return WardenPreview(
                tool_name=self.name,
                arguments=kwargs,
                preview_result="(No preview available)",
                description=f"Execute {self.name}",
            )

        if asyncio.iscoroutinefunction(self._preview_func):
            result = await self._preview_func(**kwargs)
        else:
            result = self._preview_func(**kwargs)

        # If preview returns WardenPreview, use it directly
        if isinstance(result, WardenPreview):
            return result

        # Otherwise wrap the result
        return WardenPreview(
            tool_name=self.name,
            arguments=kwargs,
            preview_result=result,
            description=f"Execute {self.name}",
        )


def warden_tool(
    func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Callable | WardenTool:
    """Decorator to create a warden tool with preview capability.

    Examples:
        ```python
        @warden_tool
        def dangerous_operation(data: str) -> str:
            '''Perform a dangerous operation.'''
            return do_something_dangerous(data)

        @dangerous_operation.preview
        def preview_dangerous(data: str) -> WardenPreview:
            return WardenPreview(
                tool_name="dangerous_operation",
                arguments={"data": data},
                preview_result=f"Will process: {data[:50]}...",
                risks=["May modify production data"],
            )
        ```
    """

    def decorator(f: Callable) -> WardenTool:
        return WardenTool(f, name=name, description=description)

    if func is not None:
        return decorator(func)
    return decorator


class Warden:
    """Manages sandboxed execution with human review.

    The Warden intercepts tool calls, runs previews, and requires
    human approval before executing dangerous operations. Approval
    is always asynchronous: the engine checkpoints and raises
    ``ExecutionInterruptedError``, and the caller resumes via
    ``agent.resume()``.

    Examples:
        ```python
        warden = Warden(
            handler=my_interrupt_handler,
            auto_approve_reversible=True,
        )

        agent = Agent(
            "openai:gpt-4o",
            tools=ToolSet([my_warden_tool, regular_tool]),
            warden=warden,
        )

        # When my_warden_tool is called:
        # 1. Preview runs first
        # 2. If reversible + auto_approve_reversible, executes inline
        # 3. Otherwise, handler is notified, checkpoint created, run pauses
        # 4. Resume with: await agent.resume(checkpoint_id, response)
        ```
    """

    def __init__(
        self,
        handler: InterruptHandler,
        auto_approve_reversible: bool = False,
    ):
        """Initialize Warden.

        Args:
            handler: InterruptHandler for human review notification.
            auto_approve_reversible: If True, auto-approve reversible actions.
        """
        self.handler = handler
        self.auto_approve_reversible = auto_approve_reversible

    async def review(
        self,
        tool: WardenTool,
        arguments: dict[str, Any],
    ) -> tuple[bool, WardenPreview]:
        """Review a tool execution for auto-approval.

        Only checks whether the action can be auto-approved (reversible
        actions when ``auto_approve_reversible`` is enabled). Does NOT
        call the handler — notification is the engine's responsibility.

        Args:
            tool: The warden tool to review.
            arguments: Arguments for the tool.

        Returns:
            Tuple of (auto_approved, preview).
        """
        # Get preview
        preview = await tool.get_preview(**arguments)

        # Auto-approve if configured and action is reversible
        if self.auto_approve_reversible and preview.reversible:
            return True, preview

        return False, preview

    def _build_prompt(self, preview: WardenPreview) -> str:
        """Build human-readable prompt from preview.

        Args:
            preview: The warden preview to format.

        Returns:
            Formatted multi-line prompt string.
        """
        lines = [
            f"🛡️ WARDEN REVIEW: {preview.tool_name}",
            "",
            f"Action: {preview.description}",
            "",
            "Arguments:",
        ]

        for key, value in preview.arguments.items():
            lines.append(f"  {key}: {value}")

        lines.extend(["", "Preview:"])
        lines.append(f"  {preview.preview_result}")

        if preview.risks:
            lines.extend(["", "⚠️ Risks:"])
            for risk in preview.risks:
                lines.append(f"  - {risk}")

        lines.append("")
        lines.append(f"Reversible: {'Yes' if preview.reversible else 'No'}")
        lines.append("")
        lines.append("Approve this action?")

        return "\n".join(lines)


class WardenToolSet(ToolSet):
    """ToolSet with Warden integration for sandboxed execution.

    Automatically handles preview and approval for warden tools.
    """

    def __init__(
        self,
        tools: list[ToolDefinition | Callable] | None = None,
        warden: Warden | None = None,
    ):
        """Initialize a WardenToolSet.

        Args:
            tools: List of tool definitions or callables.
            warden: Optional Warden instance for review integration.
        """
        super().__init__(tools)
        self.warden = warden
        self._pending_approvals: dict[str, bool] = {}

    def is_warden_tool(self, name: str) -> bool:
        """Check if a tool is a warden tool.

        Args:
            name: Tool name to check.

        Returns:
            True if the tool is a WardenTool.
        """
        tool = self.get(name)
        return isinstance(tool, WardenTool)

    async def preview(self, name: str, arguments: dict[str, Any]) -> WardenPreview | None:
        """Get preview for a warden tool.

        Args:
            name: Tool name.
            arguments: Tool arguments to preview.

        Returns:
            A WardenPreview, or None if the tool is not a warden tool.
        """
        tool = self.get(name)
        if isinstance(tool, WardenTool):
            return await tool.get_preview(**arguments)
        return None

    async def execute_with_review(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> tuple[Any, bool]:
        """Execute a tool with Warden auto-approval check if applicable.

        Only auto-approves reversible actions when configured. For
        non-auto-approved actions, returns (preview, False) so the
        caller (engine) can checkpoint and raise.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tuple of (result_or_preview, was_auto_approved).
        """
        tool = self.get(name)

        # If not a warden tool or no warden configured, execute directly
        if not isinstance(tool, WardenTool) or not self.warden:
            result = await self.execute(name, arguments)
            return result, True

        # Check auto-approval via warden
        auto_approved, preview = await self.warden.review(tool, arguments)

        if not auto_approved:
            return preview, False

        # Execute the actual tool (auto-approved)
        result = await self.execute(name, arguments)
        return result, True
