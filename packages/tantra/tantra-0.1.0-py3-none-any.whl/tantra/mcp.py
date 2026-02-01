"""MCP (Model Context Protocol) integration for Tantra.

Provides MCPTools class for connecting to MCP servers and using their tools
alongside native Tantra tools.

Examples:
    ```python
    from tantra import Agent, MCPTools

    agent = Agent(
        "openai:gpt-4o",
        tools=[
            my_native_tool,
            MCPTools("https://docs.example.com/mcp"),          # HTTP
            MCPTools(command=["npx", "mcp-server-github"]),    # Stdio
        ],
    )
    ```
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from .exceptions import MCPConnectionError, MCPError, MCPToolExecutionError

# Module-level logger for MCP operations
_mcp_logger = logging.getLogger("tantra.mcp")


class MCPToolSchema:
    """Schema for an MCP tool, mirroring the MCP protocol format."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
    ):
        """Initialize an MCP tool schema.

        Args:
            name: Tool name as registered on the MCP server.
            description: Human-readable description of the tool.
            input_schema: JSON Schema dict describing the tool's parameters.
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class MCPTransport(ABC):
    """Abstract base class for MCP transport implementations."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server.

        Raises:
            MCPConnectionError: If the connection cannot be established.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the MCP server.

        Safe to call even if not connected.
        """
        pass

    @abstractmethod
    async def list_tools(self) -> list[MCPToolSchema]:
        """Get available tools from the MCP server.

        Returns:
            List of tool schemas advertised by the server.

        Raises:
            MCPConnectionError: If not connected to the server.
        """
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Name of the tool to invoke.
            arguments: Keyword arguments for the tool.

        Returns:
            The tool's return value, typically a string or structured data.

        Raises:
            MCPConnectionError: If not connected to the server.
            MCPToolExecutionError: If the tool execution fails on the server.
        """
        pass


class StdioTransport(MCPTransport):
    """MCP transport over stdio using async subprocess."""

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        """Initialize stdio transport.

        Args:
            command: Command and arguments to launch the MCP server
                subprocess (e.g. ``["npx", "mcp-server-git"]``).
            env: Extra environment variables merged into the current
                environment before spawning the subprocess.
            timeout: Seconds to wait for a JSON-RPC response before
                raising ``MCPConnectionError``. Default ``30.0``.
        """
        self.command = command
        self.env = env
        self._timeout = timeout
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0

    async def connect(self) -> None:
        """Start the MCP server subprocess.

        Launches the command as an async subprocess, sends the MCP
        ``initialize`` handshake, and confirms with an ``initialized``
        notification.

        Raises:
            MCPConnectionError: If the subprocess fails to start or the
                handshake does not complete.
        """
        start_time = time.time()
        _mcp_logger.debug(f"MCP stdio connect starting: {self.command}")
        try:
            import os

            env = os.environ.copy()
            if self.env:
                env.update(self.env)

            # Use asyncio subprocess for non-blocking I/O
            self._process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # Send initialize request
            await self._send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "tantra", "version": "0.1.0"},
                },
            )

            # Send initialized notification
            await self._send_notification("notifications/initialized", {})

            duration_ms = (time.time() - start_time) * 1000
            _mcp_logger.info(f"MCP stdio connected: {self.command[0]} in {duration_ms:.1f}ms")

        except MCPConnectionError:
            raise
        except (OSError, TimeoutError, ValueError) as e:
            duration_ms = (time.time() - start_time) * 1000
            _mcp_logger.error(f"MCP stdio connect failed after {duration_ms:.1f}ms: {e}")
            raise MCPConnectionError(f"Failed to start MCP server: {e}")

    async def disconnect(self) -> None:
        """Stop the MCP server subprocess."""
        if self._process:
            _mcp_logger.debug(f"MCP stdio disconnecting: {self.command[0]}")
            self._process.terminate()
            await self._process.wait()
            self._process = None
            _mcp_logger.info(f"MCP stdio disconnected: {self.command[0]}")

    async def list_tools(self) -> list[MCPToolSchema]:
        """Get available tools from the MCP server.

        Returns:
            List of tool schemas advertised by the server.

        Raises:
            MCPConnectionError: If the server is not connected.
            MCPToolExecutionError: If the server returns an error response.
        """
        result = await self._send_request("tools/list", {})
        tools = []
        for tool_data in result.get("tools", []):
            tools.append(
                MCPToolSchema(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {"type": "object", "properties": {}}),
                )
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Name of the tool to invoke.
            arguments: Keyword arguments for the tool.

        Returns:
            Concatenated text content from the response, or ``None`` if
            the response contains no content blocks.

        Raises:
            MCPConnectionError: If the server is not connected.
            MCPToolExecutionError: If the server returns an error response.
        """
        start_time = time.time()
        _mcp_logger.debug(f"MCP stdio call_tool: {name} with {list(arguments.keys())}")

        result = await self._send_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

        duration_ms = (time.time() - start_time) * 1000
        _mcp_logger.info(f"MCP stdio tool '{name}' completed in {duration_ms:.1f}ms")

        # MCP returns content as a list of content blocks
        content = result.get("content", [])
        if not content:
            return None

        # Extract text content
        texts = []
        for block in content:
            if block.get("type") == "text":
                texts.append(block.get("text", ""))

        return "\n".join(texts) if texts else content

    async def _send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for response.

        Args:
            method: The JSON-RPC method name (e.g. ``"tools/list"``).
            params: Parameters dict to include in the request.

        Returns:
            The ``result`` field from the JSON-RPC response.

        Raises:
            MCPConnectionError: If the server is not connected or the
                response times out.
            MCPToolExecutionError: If the server returns a JSON-RPC error.
        """
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise MCPConnectionError("MCP server not connected")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        # Write request (async)
        request_bytes = (json.dumps(request) + "\n").encode()
        self._process.stdin.write(request_bytes)
        await self._process.stdin.drain()

        # Read response (async, with timeout)
        try:
            response_line = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=self._timeout
            )
        except TimeoutError:
            raise MCPConnectionError(f"MCP server did not respond within {self._timeout}s")

        if not response_line:
            raise MCPConnectionError("MCP server closed connection")

        response = json.loads(response_line.decode())

        if "error" in response:
            error = response["error"]
            raise MCPToolExecutionError(f"MCP error: {error.get('message', 'Unknown error')}")

        return response.get("result", {})

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send a JSON-RPC notification (no response expected).

        Args:
            method: The JSON-RPC method name.
            params: Parameters dict to include in the notification.

        Raises:
            MCPConnectionError: If the server is not connected.
        """
        if not self._process or not self._process.stdin:
            raise MCPConnectionError("MCP server not connected")

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        notification_bytes = (json.dumps(notification) + "\n").encode()
        self._process.stdin.write(notification_bytes)
        await self._process.stdin.drain()


class HTTPTransport(MCPTransport):
    """MCP transport over HTTP (Streamable HTTP)."""

    def __init__(self, url: str, headers: dict[str, str] | None = None):
        """Initialize HTTP transport.

        Args:
            url: Base URL of the MCP server (trailing slashes are stripped).
            headers: Extra HTTP headers included in every request
                (e.g. authentication tokens).
        """
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self._session_id: str | None = None
        self._client = None

    async def connect(self) -> None:
        """Initialize HTTP session with MCP server.

        Creates an ``httpx.AsyncClient`` and performs the MCP
        ``initialize`` handshake over HTTP POST.

        Raises:
            MCPError: If ``httpx`` is not installed.
            MCPConnectionError: If the HTTP request fails or the server
                returns a non-success status.
        """
        start_time = time.time()
        _mcp_logger.debug(f"MCP HTTP connect starting: {self.url}")

        import httpx

        try:
            self._client = httpx.AsyncClient()
            response = await self._client.post(
                f"{self.url}/mcp/v1/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "tantra", "version": "0.1.0"},
                },
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()
            self._session_id = result.get("sessionId")

            duration_ms = (time.time() - start_time) * 1000
            _mcp_logger.info(f"MCP HTTP connected: {self.url} in {duration_ms:.1f}ms")

        except MCPConnectionError:
            raise
        except (OSError, ValueError) as e:
            duration_ms = (time.time() - start_time) * 1000
            _mcp_logger.error(f"MCP HTTP connect failed after {duration_ms:.1f}ms: {e}")
            if self._client:
                await self._client.aclose()
                self._client = None
            raise MCPConnectionError(f"Failed to connect to MCP server at {self.url}: {e}")

    async def disconnect(self) -> None:
        """Close HTTP session."""
        _mcp_logger.debug(f"MCP HTTP disconnecting: {self.url}")
        if self._client:
            await self._client.aclose()
            self._client = None
        self._session_id = None
        _mcp_logger.info(f"MCP HTTP disconnected: {self.url}")

    async def list_tools(self) -> list[MCPToolSchema]:
        """Get available tools from the MCP server.

        Returns:
            List of tool schemas advertised by the server.

        Raises:
            MCPConnectionError: If not connected to the server.
        """
        if not self._client:
            raise MCPConnectionError("Not connected. Call connect() first.")

        response = await self._client.post(
            f"{self.url}/mcp/v1/tools/list",
            json={},
            headers=self._get_headers(),
        )
        response.raise_for_status()
        result = response.json()

        tools = []
        for tool_data in result.get("tools", []):
            tools.append(
                MCPToolSchema(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {"type": "object", "properties": {}}),
                )
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Name of the tool to invoke.
            arguments: Keyword arguments for the tool.

        Returns:
            Concatenated text content from the response, or ``None`` if
            the response contains no content blocks.

        Raises:
            MCPConnectionError: If not connected to the server.
        """
        start_time = time.time()
        _mcp_logger.debug(f"MCP HTTP call_tool: {name} with {list(arguments.keys())}")

        if not self._client:
            raise MCPConnectionError("Not connected. Call connect() first.")

        response = await self._client.post(
            f"{self.url}/mcp/v1/tools/call",
            json={"name": name, "arguments": arguments},
            headers=self._get_headers(),
        )
        response.raise_for_status()
        result = response.json()

        duration_ms = (time.time() - start_time) * 1000
        _mcp_logger.info(f"MCP HTTP tool '{name}' completed in {duration_ms:.1f}ms")

        content = result.get("content", [])
        if not content:
            return None

        texts = []
        for block in content:
            if block.get("type") == "text":
                texts.append(block.get("text", ""))

        return "\n".join(texts) if texts else content

    def _get_headers(self) -> dict[str, str]:
        """Get headers including session ID if available.

        Returns:
            Merged headers dict containing user-supplied headers and,
            when present, the ``X-MCP-Session-ID`` header.
        """
        headers = self.headers.copy()
        if self._session_id:
            headers["X-MCP-Session-ID"] = self._session_id
        return headers


class MCPToolDefinition:
    """Wrapper that makes an MCP tool look like a native ToolDefinition.

    This allows MCP tools to be used interchangeably with native tools
    in the ToolSet and execution engine.
    """

    def __init__(
        self,
        schema: MCPToolSchema,
        transport: MCPTransport,
        trace_callback: Callable[[str, dict, Any, float, bool], None] | None = None,
    ):
        """Initialize an MCP tool definition.

        Args:
            schema: The tool's name, description, and input schema.
            transport: The MCP transport used to execute the tool.
            trace_callback: Optional callback invoked after every
                execution. The positional arguments are:
                ``(tool_name: str, arguments: dict, result: Any,
                duration_ms: float, success: bool)``.
        """
        self.schema = schema
        self.transport = transport
        self.trace_callback = trace_callback

        # Mimic ToolDefinition interface
        self.name = schema.name
        self.description = schema.description
        self.is_async = True
        self.interrupt = None  # MCP tools don't support interrupts (yet)

        # Track last execution duration for observability
        self.last_duration_ms: float = 0.0

    @property
    def requires_interrupt(self) -> bool:
        """MCP tools don't support interrupts."""
        return False

    def get_schema(self) -> dict[str, Any]:
        """Get OpenAI-compatible schema."""
        return self.schema.to_openai_schema()

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool via MCP transport.

        Args:
            **kwargs: Tool arguments matching the tool's input schema.

        Returns:
            The tool's return value from the MCP server.

        Raises:
            MCPToolExecutionError: If the tool execution fails on the
                server or a transport error occurs.
        """
        start_time = time.time()
        success = False
        result = None

        try:
            result = await self.transport.call_tool(self.name, kwargs)
            success = True
            return result
        except MCPToolExecutionError:
            raise
        except (MCPError, OSError, ValueError, TimeoutError) as e:
            _mcp_logger.error(f"MCP tool '{self.name}' execution failed: {e}")
            raise MCPToolExecutionError(f"MCP tool '{self.name}' failed: {e}")
        finally:
            self.last_duration_ms = (time.time() - start_time) * 1000
            _mcp_logger.debug(
                f"MCP tool '{self.name}' finished: success={success}, duration={self.last_duration_ms:.1f}ms"
            )
            # Call trace callback if provided
            if self.trace_callback:
                try:
                    self.trace_callback(self.name, kwargs, result, self.last_duration_ms, success)
                except Exception:
                    pass  # Don't let callback errors break execution


def _run_sync(coro: Any) -> Any:
    """Run a coroutine synchronously, handling existing event loops.

    Args:
        coro: An awaitable coroutine object to execute.

    Returns:
        The value returned by the coroutine.

    Raises:
        RuntimeError: If called from an async context without
            ``nest_asyncio`` installed.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)

    # Already in async context - use nest_asyncio
    import nest_asyncio

    nest_asyncio.apply()
    return asyncio.run(coro)


class MCPTools:
    """Connects to an MCP server and exposes its tools.

    MCPTools can be passed to ToolSet alongside native tools. The tools
    are discovered on initialization and routed to the MCP server on execution.

    Examples:
        ```python
        # HTTP transport (remote server)
        mcp = MCPTools("https://docs.example.com/mcp")

        # Stdio transport (local subprocess)
        mcp = MCPTools(command=["npx", "-y", "@modelcontextprotocol/server-git"])

        # Use in agent
        agent = Agent("openai:gpt-4o", tools=[native_tool, mcp])

        # In async context, use lazy mode:
        mcp = MCPTools("https://example.com/mcp", lazy=True)
        await mcp.ensure_connected()
        ```
    """

    def __init__(
        self,
        url: str | None = None,
        command: list[str] | None = None,
        env: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        lazy: bool = False,
    ):
        """Initialize MCPTools.

        Args:
            url: URL for HTTP transport (e.g., "https://docs.example.com/mcp").
            command: Command for stdio transport (e.g., ["npx", "mcp-server-git"]).
            env: Environment variables for stdio transport.
            headers: HTTP headers for HTTP transport.
            lazy: If True, don't connect until first use. Default is False.
                  Use lazy=True when calling from async context.

        Raises:
            ValueError: If neither url nor command is provided.
            MCPConnectionError: If connection fails (unless lazy=True).
            RuntimeError: If called from async context without lazy=True.
        """
        if url is None and command is None:
            raise ValueError("Provide either url or command")

        if url is not None:
            self._transport: MCPTransport = HTTPTransport(url, headers)
        else:
            self._transport = StdioTransport(command, env)

        self._tools: list[MCPToolDefinition] = []
        self._connected = False
        self._lazy = lazy

        if not lazy:
            _run_sync(self._connect_and_discover())

    async def _connect_and_discover(self) -> None:
        """Connect to server and discover tools."""
        if self._connected:
            return

        await self._transport.connect()
        schemas = await self._transport.list_tools()
        self._tools = [MCPToolDefinition(schema, self._transport) for schema in schemas]
        self._connected = True

    async def ensure_connected(self) -> None:
        """Ensure connection is established (for lazy mode).

        No-op if already connected. Otherwise connects and discovers
        tools from the MCP server.

        Raises:
            MCPConnectionError: If the connection cannot be established.
        """
        if not self._connected:
            await self._connect_and_discover()

    def __iter__(self):
        """Iterate over tool definitions."""
        return iter(self._tools)

    def __len__(self) -> int:
        """Number of tools."""
        return len(self._tools)

    @property
    def tool_names(self) -> list[str]:
        """Names of all available tools."""
        return [t.name for t in self._tools]

    async def call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool by name.

        Args:
            name: Name of the tool to invoke.
            arguments: Keyword arguments for the tool.

        Returns:
            The tool's return value from the MCP server.
        """
        await self.ensure_connected()
        return await self._transport.call_tool(name, arguments)

    async def close(self) -> None:
        """Close the connection."""
        if self._connected:
            await self._transport.disconnect()
            self._connected = False

    def __repr__(self) -> str:
        transport_type = type(self._transport).__name__
        return f"MCPTools({transport_type}, tools={len(self._tools)})"
