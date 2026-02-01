"""Tests for the tool framework."""

import pytest

from tantra import ToolDefinition, ToolSet, tool
from tantra.exceptions import ToolExecutionError, ToolNotFoundError, ToolValidationError


class TestToolDecorator:
    """Tests for the @tool decorator."""

    def test_basic_tool(self):
        """Basic tool creation from function."""

        @tool
        def my_tool(arg: str) -> str:
            """My tool description."""
            return arg

        assert isinstance(my_tool, ToolDefinition)
        assert my_tool.name == "my_tool"
        assert my_tool.description == "My tool description."

    def test_tool_with_custom_name(self):
        """Tool with custom name."""

        @tool(name="custom_name")
        def my_tool() -> str:
            return "done"

        assert my_tool.name == "custom_name"

    def test_tool_with_custom_description(self):
        """Tool with custom description."""

        @tool(description="Custom description")
        def my_tool() -> str:
            """Original docstring."""
            return "done"

        assert my_tool.description == "Custom description"

    def test_tool_schema_generation(self):
        """Tool generates valid OpenAI schema."""

        @tool
        def calculate(a: int, b: int, operation: str = "add") -> int:
            """Calculate two numbers.

            Args:
                a: First number.
                b: Second number.
                operation: The operation to perform.
            """
            return a + b

        schema = calculate.get_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "calculate"
        assert schema["function"]["description"] == "Calculate two numbers."

        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "a" in params["properties"]
        assert "b" in params["properties"]
        assert "operation" in params["properties"]
        assert params["properties"]["a"]["type"] == "integer"
        assert params["properties"]["b"]["type"] == "integer"
        assert params["properties"]["operation"]["type"] == "string"
        assert "a" in params["required"]
        assert "b" in params["required"]
        assert "operation" not in params["required"]  # Has default

    def test_tool_with_docstring_args(self):
        """Tool extracts argument descriptions from docstring."""

        @tool
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet a person.

            Args:
                name: The person's name.
                greeting: The greeting to use.
            """
            return f"{greeting}, {name}!"

        schema = greet.get_schema()
        props = schema["function"]["parameters"]["properties"]

        assert props["name"]["description"] == "The person's name."
        assert "The greeting to use." in props["greeting"]["description"]


class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_sync_tool_execution(self):
        """Execute a sync tool."""

        @tool
        def add(a: int, b: int) -> int:
            return a + b

        result = await add.execute(a=2, b=3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Execute an async tool."""

        @tool
        async def async_add(a: int, b: int) -> int:
            return a + b

        result = await async_add.execute(a=2, b=3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_tool_with_defaults(self):
        """Execute tool with default arguments."""

        @tool
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        result = await greet.execute(name="World")
        assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_tool_validation_error(self):
        """Tool raises ToolValidationError for invalid args."""

        @tool
        def add(a: int, b: int) -> int:
            return a + b

        with pytest.raises(ToolValidationError):
            await add.execute(a=1)  # Missing 'b'

    @pytest.mark.asyncio
    async def test_tool_execution_error(self):
        """Tool raises ToolExecutionError on failure."""

        @tool
        def failing_tool() -> str:
            raise ValueError("Something went wrong")

        with pytest.raises(ToolExecutionError):
            await failing_tool.execute()

    def test_sync_execution(self):
        """Execute tool synchronously."""

        @tool
        def multiply(a: int, b: int) -> int:
            return a * b

        result = multiply.execute_sync(a=3, b=4)
        assert result == 12


class TestToolSet:
    """Tests for ToolSet."""

    def test_create_empty_toolset(self):
        """Create empty ToolSet."""
        tools = ToolSet()
        assert len(tools) == 0

    def test_create_with_tools(self):
        """Create ToolSet with tools."""

        @tool
        def tool1() -> str:
            return "1"

        @tool
        def tool2() -> str:
            return "2"

        tools = ToolSet([tool1, tool2])
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_add_tool(self):
        """Add tool to ToolSet."""
        tools = ToolSet()

        @tool
        def my_tool() -> str:
            return "done"

        tools.add(my_tool)
        assert "my_tool" in tools

    def test_add_plain_function(self):
        """Add plain function (auto-wrapped)."""
        tools = ToolSet()

        def plain_func(x: int) -> int:
            return x * 2

        tools.add(plain_func)
        assert "plain_func" in tools

    def test_get_tool(self):
        """Get tool by name."""

        @tool
        def my_tool() -> str:
            return "done"

        tools = ToolSet([my_tool])
        retrieved = tools.get("my_tool")
        assert retrieved.name == "my_tool"

    def test_get_nonexistent_tool(self):
        """Get nonexistent tool raises error."""
        tools = ToolSet()

        with pytest.raises(ToolNotFoundError):
            tools.get("nonexistent")

    def test_get_schemas(self):
        """Get schemas for all tools."""

        @tool
        def tool1(x: int) -> int:
            return x

        @tool
        def tool2(y: str) -> str:
            return y

        tools = ToolSet([tool1, tool2])
        schemas = tools.get_schemas()

        assert len(schemas) == 2
        names = [s["function"]["name"] for s in schemas]
        assert "tool1" in names
        assert "tool2" in names

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Execute tool by name."""

        @tool
        def add(a: int, b: int) -> int:
            return a + b

        tools = ToolSet([add])
        result = await tools.execute("add", {"a": 5, "b": 3})
        assert result == 8

    def test_names_property(self):
        """Get list of tool names."""

        @tool
        def alpha() -> str:
            return "a"

        @tool
        def beta() -> str:
            return "b"

        tools = ToolSet([alpha, beta])
        assert set(tools.names) == {"alpha", "beta"}

    def test_iteration(self):
        """Iterate over tools."""

        @tool
        def t1() -> str:
            return "1"

        @tool
        def t2() -> str:
            return "2"

        tools = ToolSet([t1, t2])
        names = [t.name for t in tools]
        assert set(names) == {"t1", "t2"}
