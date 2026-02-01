"""Tantra exception hierarchy.

All Tantra exceptions inherit from TantraError for easy catching.
"""

from __future__ import annotations

from typing import Any


class TantraError(Exception):
    """Base exception for all Tantra errors."""

    pass


class ProviderError(TantraError):
    """Error from the LLM provider.

    Attributes:
        provider: Name of the provider that raised the error, or None.
    """

    def __init__(self, message: str, provider: str | None = None):
        """Initialize ProviderError.

        Args:
            message: Human-readable error description.
            provider: Name of the provider (e.g. ``"openai"``, ``"anthropic"``).
        """
        self.provider = provider
        super().__init__(f"[{provider}] {message}" if provider else message)


class ToolError(TantraError):
    """Error during tool execution.

    Attributes:
        tool_name: Name of the tool that caused the error, or None.
    """

    def __init__(self, message: str, tool_name: str | None = None):
        """Initialize ToolError.

        Args:
            message: Human-readable error description.
            tool_name: Name of the tool that caused the error.
        """
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}': {message}" if tool_name else message)


class ToolNotFoundError(ToolError):
    """Requested tool was not found in the ToolSet."""

    def __init__(self, tool_name: str):
        """Initialize ToolNotFoundError.

        Args:
            tool_name: Name of the tool that was not found.
        """
        super().__init__("not found", tool_name=tool_name)


class ToolValidationError(ToolError):
    """Tool arguments failed validation."""

    def __init__(self, tool_name: str, details: str):
        """Initialize ToolValidationError.

        Args:
            tool_name: Name of the tool whose arguments are invalid.
            details: Description of the validation failure.
        """
        super().__init__(f"validation failed - {details}", tool_name=tool_name)


class ToolExecutionError(ToolError):
    """Tool execution raised an exception.

    Attributes:
        original_error: The exception raised by the tool function.
    """

    def __init__(self, tool_name: str, original_error: Exception):
        """Initialize ToolExecutionError.

        Args:
            tool_name: Name of the tool that failed.
            original_error: The underlying exception from the tool function.
        """
        self.original_error = original_error
        super().__init__(f"execution failed - {original_error}", tool_name=tool_name)


class ConfigurationError(TantraError):
    """Invalid configuration provided."""

    pass


class MaxIterationsError(TantraError):
    """Agent exceeded maximum iterations.

    Attributes:
        max_iterations: The iteration limit that was exceeded.
    """

    def __init__(self, max_iterations: int):
        """Initialize MaxIterationsError.

        Args:
            max_iterations: The iteration limit that was exceeded.
        """
        self.max_iterations = max_iterations
        super().__init__(f"Agent exceeded maximum iterations ({max_iterations})")


class TantraMemoryError(TantraError):
    """Error in memory operations."""

    pass


class MCPError(TantraError):
    """Base error for MCP-related issues."""

    pass


class MCPConnectionError(MCPError):
    """Failed to connect to MCP server."""

    def __init__(self, message: str):
        """Initialize MCPConnectionError.

        Args:
            message: Description of the connection failure.
        """
        super().__init__(f"MCP connection failed: {message}")


class MCPToolExecutionError(MCPError):
    """MCP tool execution failed."""

    def __init__(self, message: str):
        """Initialize MCPToolExecutionError.

        Args:
            message: Description of the execution failure.
        """
        super().__init__(message)


class ContextMergeConflictError(TantraError):
    """Two parallel agents wrote different values to the same context key.

    Attributes:
        key: The context key with conflicting writes.
        agents: Names of the agents that wrote different values.
        values: The conflicting values written by each agent.
    """

    def __init__(self, key: str, agents: list[str], values: list[Any]):
        """Initialize ContextMergeConflictError.

        Args:
            key: The context key with conflicting writes.
            agents: Names of the agents that wrote different values.
            values: The conflicting values written by each agent.
        """
        self.key = key
        self.agents = agents
        self.values = values
        agent_list = ", ".join(agents)
        super().__init__(
            f"Context merge conflict on key '{key}': agents [{agent_list}] wrote different values"
        )
