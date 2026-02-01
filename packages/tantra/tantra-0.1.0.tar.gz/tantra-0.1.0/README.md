# Tantra

**A simple, minimal, observable, production-ready AI agent framework.**

Tantra is designed for developers who build AI agents for production. It combines simplicity with powerful features including first-class observability, integrated evaluation, and extensible provider support.

## Features

- **Minimal by Default** - Optional modules for advanced features
- **Observable by Design** - Every operation produces structured logs with cost tracking
- **Testable First** - Integrated evaluation framework as easy as writing unit tests
- **Type-Safe** - Full type hints with Pydantic models
- **Extensible** - Plugin architecture for custom LLM providers

## Installation

```bash
pip install tantra
```

Or install from source:

```bash
git clone https://github.com/tantra-run/tantra-py.git
cd tantra
pip install -e ".[dev]"
```

## Quick Start

### Simple Agent

```python
import asyncio
from tantra import Agent

async def main():
    agent = Agent(
        "openai:gpt-4o",
        system_prompt="You are a helpful assistant."
    )

    result = await agent.run("Hello!")
    print(result.output)
    print(f"Cost: ${result.metadata.estimated_cost:.4f}")

asyncio.run(main())
```

### Agent with Tools

```python
import asyncio
from tantra import Agent, tool, ToolSet

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city.
    """
    return f"Weather in {city}: Sunny, 72F"

async def main():
    agent = Agent(
        "openai:gpt-4o",
        tools=ToolSet([get_weather]),
        system_prompt="You can check weather for users."
    )

    result = await agent.run("What's the weather in Tokyo?")
    print(result.output)

asyncio.run(main())
```

### Evaluation

```python
import asyncio
from tantra import Agent, TestCase, EvaluationSuite, contains, tool_called

async def main():
    agent = Agent("openai:gpt-4o-mini")

    suite = EvaluationSuite()
    suite.add_test(TestCase(
        input="What is 2 + 2?",
        matchers=[contains("4")]
    ))

    results = await suite.run(agent)
    print(f"Passed: {results.passed}/{results.metrics.total_tests}")

asyncio.run(main())
```

## Core Concepts

### Agent

The `Agent` class is the main entry point. It wraps an LLM provider, tools, and memory.

```python
agent = Agent(
    provider="openai:gpt-4o",  # or a ModelProvider instance
    tools=ToolSet([...]),      # optional tools
    system_prompt="...",       # agent behavior
    memory=ConversationMemory(), # conversation history
    max_iterations=10,         # prevent infinite loops
)
```

### Tools

Tools are defined using the `@tool` decorator. Type hints and docstrings are automatically converted to OpenAI-compatible schemas.

```python
@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression.

    Args:
        expression: A mathematical expression like "2 + 2".
    """
    return str(eval(expression))
```

### Memory

Memory stores conversation history. The built-in `ConversationMemory` keeps messages in memory.

```python
from tantra import ConversationMemory, WindowedMemory

# Keep all messages
memory = ConversationMemory()

# Keep only last N messages
memory = WindowedMemory(window_size=10)
```

### Observability

Every agent run produces a trace of `LogEntry` objects with full visibility into:
- Prompts sent to the LLM
- LLM responses
- Tool calls and results
- Token usage and cost

```python
result = await agent.run("Hello!")

for entry in result.trace:
    print(f"[{entry.type}] {entry.data}")

print(f"Total cost: ${result.metadata.estimated_cost:.4f}")
```

### Evaluation

The evaluation framework makes testing agents as easy as unit tests:

```python
suite = EvaluationSuite()
suite.add_test(TestCase(
    input="What's the capital of France?",
    matchers=[
        contains("Paris"),
        cost_under(0.01),
    ]
))

results = await suite.run(agent)
```

Built-in matchers:
- `contains(text)` - Output contains substring
- `not_contains(text)` - Output does not contain substring
- `matches_regex(pattern)` - Output matches regex
- `json_valid()` - Output is valid JSON
- `json_schema(schema)` - Output matches JSON schema
- `tool_called(name)` - Tool was called
- `tool_not_called(name)` - Tool was not called
- `cost_under(amount)` - Cost below threshold
- `tokens_under(count)` - Tokens below threshold

## Custom Providers

Create custom providers by implementing the `ModelProvider` interface:

```python
from tantra import ModelProvider, Message, ProviderResponse

class MyProvider(ModelProvider):
    async def complete(self, messages, tools=None, **kwargs):
        # Call your LLM API
        return ProviderResponse(content="Hello!")

    def count_tokens(self, messages):
        return len(str(messages))

    @property
    def model_name(self):
        return "my-model"

    @property
    def cost_per_1k_input(self):
        return 0.001

    @property
    def cost_per_1k_output(self):
        return 0.002
```

## Examples

See the `examples/` directory for complete examples:

- `01_simple_agent.py` - Basic agent without tools
- `02_tool_agent.py` - Agent with tools
- `03_streaming.py` - Streaming execution
- `04_evaluation.py` - Testing agents
- `05_custom_provider.py` - Custom LLM provider

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .

# Lint
ruff check .
```

## License

MIT
