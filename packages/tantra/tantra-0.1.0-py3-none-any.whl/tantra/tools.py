"""Tool framework for Tantra.

Provides the @tool decorator for defining tools and ToolSet for managing collections.
Tools are automatically converted to OpenAI-compatible JSON schemas.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any, get_type_hints

from .context import RunContext
from .exceptions import ToolExecutionError, ToolNotFoundError, ToolValidationError

# Module-level logger for tool operations
_tools_logger = logging.getLogger("tantra.tools")

# Type mapping from Python types to JSON schema types
TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _get_json_type(python_type: type) -> str:
    """Convert a Python type annotation to a JSON Schema type string.

    Args:
        python_type: The Python type to convert.

    Returns:
        JSON Schema type string (e.g. ``"string"``, ``"integer"``).
    """
    # Handle Optional types
    origin = getattr(python_type, "__origin__", None)
    if origin is type(None):
        return "null"

    # Handle Union types (including Optional)
    if origin is not None:
        # For Union, get the first non-None type
        args = getattr(python_type, "__args__", ())
        for arg in args:
            if arg is not type(None):
                return _get_json_type(arg)

    return TYPE_MAP.get(python_type, "string")


def _parse_docstring(docstring: str | None) -> tuple[str, dict[str, str]]:
    """Parse a docstring to extract description and argument descriptions.

    Supports Google-style docstrings:
        Description here.

        Args:
            arg1: Description of arg1.
            arg2: Description of arg2.

    Returns:
        Tuple of (main_description, {arg_name: arg_description})
    """
    if not docstring:
        return "", {}

    lines = docstring.strip().split("\n")
    description_lines = []
    arg_descriptions: dict[str, str] = {}

    in_args_section = False
    current_arg: str | None = None
    current_desc: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Check for Args: section
        if stripped.lower() in ("args:", "arguments:", "parameters:"):
            in_args_section = True
            continue

        # Check for end of Args section (new section or empty line after content)
        if in_args_section and stripped and ":" in stripped and not stripped.startswith(" "):
            # Check if it's a new section header
            if stripped.lower() in ("returns:", "raises:", "yields:", "examples:"):
                in_args_section = False
                if current_arg and current_desc:
                    arg_descriptions[current_arg] = " ".join(current_desc).strip()
                continue

        if in_args_section:
            # Check for new argument
            if (
                ":" in stripped
                and not stripped.startswith(" ")
                or (":" in stripped and current_arg is None)
            ):
                # Save previous argument if exists
                if current_arg and current_desc:
                    arg_descriptions[current_arg] = " ".join(current_desc).strip()

                # Parse new argument
                parts = stripped.split(":", 1)
                current_arg = parts[0].strip()
                current_desc = [parts[1].strip()] if len(parts) > 1 else []
            elif current_arg:
                # Continuation of current argument description
                current_desc.append(stripped)
        else:
            # Main description
            if stripped:
                description_lines.append(stripped)

    # Save last argument
    if current_arg and current_desc:
        arg_descriptions[current_arg] = " ".join(current_desc).strip()

    return " ".join(description_lines), arg_descriptions


class ToolDefinition:
    """Holds metadata about a tool function."""

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
        interrupt: str | None = None,
    ):
        """Initialize a ToolDefinition.

        Args:
            func: The function to wrap as a tool.
            name: Custom tool name. Defaults to ``func.__name__``.
            description: Custom description. Defaults to the function's docstring.
            interrupt: If set, execution pauses for human approval. The string
                      is shown as the approval prompt.
        """
        self.func = func
        self.name = name or func.__name__
        self._explicit_description = description

        # Interrupt configuration
        # If set, execution pauses and waits for human input before running
        self.interrupt = interrupt

        # Parse function signature
        self.signature = inspect.signature(func)
        self.type_hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

        # Parse docstring
        doc_description, self.arg_descriptions = _parse_docstring(func.__doc__)
        self.description = description or doc_description or f"Execute the {self.name} tool"

        # Check if function is async
        self.is_async = asyncio.iscoroutinefunction(func)

        # Check if function accepts context parameter (by type annotation)
        self.accepts_context = self.type_hints.get("context") is RunContext

    @property
    def requires_interrupt(self) -> bool:
        """Whether this tool requires human approval before execution."""
        return self.interrupt is not None

    def get_schema(self) -> dict[str, Any]:
        """Generate OpenAI-compatible tool schema.

        Returns:
            A dict with ``type``, ``function.name``, ``function.description``,
            and ``function.parameters`` keys.
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in self.signature.parameters.items():
            if param_name == "self":
                continue
            # Skip interrupt_response - it's injected by engine, not LLM
            if param_name == "interrupt_response":
                continue
            # Skip context if typed as RunContext - injected by engine, not LLM
            if param_name == "context" and self.accepts_context:
                continue

            # Get type
            param_type = self.type_hints.get(param_name, str)
            json_type = _get_json_type(param_type)

            # Build property schema
            prop_schema: dict[str, Any] = {"type": json_type}

            # Add description from docstring
            if param_name in self.arg_descriptions:
                prop_schema["description"] = self.arg_descriptions[param_name]

            # Handle default values
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            else:
                # Include default in description if it exists
                if param.default is not None:
                    desc = prop_schema.get("description", "")
                    if desc:
                        prop_schema["description"] = f"{desc} (default: {param.default})"

            properties[param_name] = prop_schema

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    async def execute(
        self,
        context: RunContext | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute the tool with the given arguments.

        Args:
            context: Optional RunContext for shared state.
                    Injected into tool if it accepts this parameter.
            **kwargs: Arguments to pass to the tool function.

        Returns:
            The tool function's return value.

        Raises:
            ToolValidationError: If arguments don't match the function signature.
            ToolExecutionError: If the function raises an exception.
        """
        # Inject context if tool accepts it
        if self.accepts_context and context is not None:
            kwargs["context"] = context

        # Validate arguments against signature
        try:
            bound = self.signature.bind(**kwargs)
            bound.apply_defaults()
        except TypeError as e:
            _tools_logger.warning(
                f"Tool validation error: tool={self.name}, error={e}, args={list(kwargs.keys())}"
            )
            raise ToolValidationError(self.name, str(e))

        # Execute the function
        try:
            if self.is_async:
                return await self.func(**kwargs)
            else:
                return self.func(**kwargs)
        except Exception as e:
            raise ToolExecutionError(self.name, e)

    def execute_sync(self, **kwargs: Any) -> Any:
        """Execute the tool synchronously.

        Args:
            **kwargs: Arguments to pass to the tool function.

        Returns:
            The tool function's return value.

        Raises:
            ToolValidationError: If arguments don't match the function signature.
            ToolExecutionError: If the function raises or is async.
        """
        # Validate arguments against signature
        try:
            bound = self.signature.bind(**kwargs)
            bound.apply_defaults()
        except TypeError as e:
            _tools_logger.warning(
                f"Tool validation error: tool={self.name}, error={e}, args={list(kwargs.keys())}"
            )
            raise ToolValidationError(self.name, str(e))

        # Execute the function
        try:
            if self.is_async:
                raise ToolExecutionError(
                    self.name, RuntimeError("Cannot run async tool synchronously")
                )
            return self.func(**kwargs)
        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(self.name, e)


def tool(
    func: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    interrupt: str | None = None,
) -> Callable | ToolDefinition:
    """Decorator to mark a function as a tool.

    Can be used with or without arguments:

        @tool
        def my_tool(arg: str) -> str:
            '''Tool description.'''
            return arg

        @tool(name="custom_name", description="Custom description")
        def another_tool(arg: int) -> int:
            return arg * 2

        @tool(interrupt="Approve this deletion?")
        def delete_user(user_id: int) -> bool:
            '''Delete a user. Requires human approval.'''
            db.delete(user_id)
            return True

    Args:
        func: The function to decorate (when used without parentheses).
        name: Optional custom name for the tool (defaults to function name).
        description: Optional description (defaults to docstring).
        interrupt: If set, pause execution and prompt human before running.
                   The string is the prompt shown to the human.

    Returns:
        ToolDefinition wrapping the function.
    """

    def decorator(f: Callable) -> ToolDefinition:
        return ToolDefinition(f, name=name, description=description, interrupt=interrupt)

    if func is not None:
        # Decorator used without parentheses: @tool
        return decorator(func)
    else:
        # Decorator used with arguments: @tool(name="...")
        return decorator


class ToolSet:
    """A collection of tools that can be used by an agent.

    Manages tool registration, schema generation, and execution.
    Supports both native tools and MCP tools.

    Examples:
        ```python
        from tantra import ToolSet, tool, MCPTools

        @tool
        def my_tool(x: str) -> str:
            return x

        tools = ToolSet([
            my_tool,                                           # Native tool
            MCPTools("https://docs.example.com/mcp"),          # MCP server
        ])
        ```
    """

    def __init__(self, tools: list | None = None):
        """Initialize the ToolSet.

        Args:
            tools: Optional list of tools to add. Can be:
                   - ToolDefinition objects
                   - Decorated functions (@tool)
                   - MCPTools instances (all tools from server are added)
        """
        self._tools: dict[str, ToolDefinition] = {}

        if tools:
            for t in tools:
                self.add(t)

    def add(self, tool_or_func: Any) -> None:
        """Add a tool to the set.

        Args:
            tool_or_func: Can be:
                - ToolDefinition: Added directly
                - Callable: Wrapped in ToolDefinition
                - MCPTools: All tools from the MCP server are added
                - MCPToolDefinition: Added directly (MCP tool wrapper)
        """
        # Import here to avoid circular import
        from .mcp import MCPToolDefinition, MCPTools

        if isinstance(tool_or_func, MCPTools):
            # Add all tools from the MCP server
            for mcp_tool in tool_or_func:
                self._tools[mcp_tool.name] = mcp_tool
        elif isinstance(tool_or_func, MCPToolDefinition):
            # Single MCP tool
            self._tools[tool_or_func.name] = tool_or_func
        elif isinstance(tool_or_func, ToolDefinition):
            self._tools[tool_or_func.name] = tool_or_func
        else:
            # Assume it's a callable
            tool_def = ToolDefinition(tool_or_func)
            self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> ToolDefinition:
        """Get a tool by name.

        Args:
            name: The tool name.

        Returns:
            The tool (ToolDefinition or MCPToolDefinition).

        Raises:
            ToolNotFoundError: If tool is not in the set.
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI-compatible schemas for all tools.

        Returns:
            List of tool schemas ready for the OpenAI API.
        """
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: RunContext | None = None,
    ) -> Any:
        """Execute a tool by name.

        Args:
            name: The tool name.
            arguments: Arguments to pass to the tool.
            context: Optional RunContext for shared state.

        Returns:
            The tool's return value.

        Raises:
            ToolNotFoundError: If tool is not in the set.
            ToolValidationError: If arguments are invalid.
            ToolExecutionError: If tool execution fails.
        """
        tool_def = self.get(name)

        if isinstance(tool_def, ToolDefinition):
            return await tool_def.execute(context=context, **arguments)
        else:
            # MCPToolDefinition or other tools without context support
            return await tool_def.execute(**arguments)

    def execute_sync(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool synchronously.

        Args:
            name: The tool name.
            arguments: Arguments to pass to the tool.

        Returns:
            The tool's return value.

        Raises:
            ToolNotFoundError: If tool is not in the set.
            ToolValidationError: If arguments are invalid.
            ToolExecutionError: If tool execution fails.
        """
        tool_def = self.get(name)
        return tool_def.execute_sync(**arguments)

    @property
    def names(self) -> list[str]:
        """Get list of tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        """Return the number of tools in this set."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check whether a tool with the given name exists."""
        return name in self._tools

    def __iter__(self) -> iter:
        """Iterate over all ToolDefinition objects in this set."""
        return iter(self._tools.values())
