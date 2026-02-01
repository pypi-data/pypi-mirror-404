"""In-the-loop components for Tantra.

Provides in-the-loop functionality including interrupts,
agent registry, and the Warden pattern.

Example:
    from tantra.intheloop import (
        Interrupt, InterruptResponse, InterruptHandler,
        AgentRegistry, Warden, warden_tool,
    )

    # Set up interrupt handler
    handler = CallbackInterruptHandler(my_notify_fn)

    # Create warden for tool review
    warden = Warden(handler=handler)

    # Use with agent
    agent = Agent(
        "openai:gpt-4o",
        tools=ToolSet([my_tool]),
        interrupt_handler=handler,
    )
"""

# Base classes
from .base import (
    CallbackInterruptHandler,
    Interrupt,
    InterruptHandler,
    InterruptResponse,
)

# Registry
from .registry import (
    AgentRegistry,
    default_registry,
    get_agent,
    register_agent,
)

# Warden Pattern
from .warden import (
    Warden,
    WardenPreview,
    WardenTool,
    WardenToolSet,
    warden_tool,
)

__all__ = [
    # Interrupts
    "Interrupt",
    "InterruptResponse",
    "InterruptHandler",
    "CallbackInterruptHandler",
    # Registry
    "AgentRegistry",
    "default_registry",
    "register_agent",
    "get_agent",
    # Warden
    "Warden",
    "WardenTool",
    "WardenPreview",
    "WardenToolSet",
    "warden_tool",
]
