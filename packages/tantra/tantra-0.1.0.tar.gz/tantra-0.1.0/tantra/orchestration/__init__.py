"""Multi-Agent Orchestration for Tantra.

Provides patterns for coordinating multiple agents:
- Pipeline: Sequential execution, output flows to next agent
- Router: Route requests to appropriate agent
- Parallel: Run agents concurrently and combine results
- Graph: Workflow engine with conditional edges and cycles
- Swarm: Dynamic agent handoffs with context preservation

Example:
    from tantra import Pipeline, Router, Parallel
    from tantra import Graph, GraphBuilder, Swarm
    from tantra import chain, fan_out, select, swarm

    # Pipeline: sequential execution
    result = await chain(agent1, agent2, agent3).run("input")

    # Router: conditional routing
    router = select(
        {"billing": billing_agent, "support": support_agent},
        route_fn=lambda x: "billing" if "bill" in x else "support",
    )
    result = await router.run("billing question")

    # Parallel: concurrent execution
    result = await fan_out(agent1, agent2, agent3).run("analyze this")

    # Graph: workflow engine
    graph = (
        GraphBuilder("workflow")
        .add_agent("research", researcher)
        .add_agent("write", writer)
        .edge("START", "research")
        .edge("research", "write")
        .edge("write", "END")
        .build()
    )
    result = await graph.run("Write about AI")

    # Swarm: dynamic handoffs
    swarm = Swarm(
        agents={"triage": triage, "billing": billing},
        entry_point="triage",
    )
    result = await swarm.run("I need a refund")
"""

# Base types and classes
from .base import (
    AgentStep,
    OrchestrationDetail,
    Orchestrator,
)

# Graph-based workflow engine
from .graph import (
    AgentNode,
    Edge,
    EdgeCondition,
    FunctionNode,
    Graph,
    GraphBuilder,
    GraphDetail,
    GraphState,
    Node,
    NodeType,
    RouterNode,
    create_graph,
)

# Parallel pattern
from .parallel import (
    Parallel,
    fan_out,
)

# Pipeline pattern
from .pipeline import (
    Pipeline,
    chain,
)

# Router pattern
from .router import (
    Router,
    select,
)

# Solo orchestrator
from .solo import Solo

# Swarm orchestration
from .swarm import (
    Handoff,
    Swarm,
    SwarmDetail,
    SwarmStep,
    swarm,
)

__all__ = [
    # Base
    "Orchestrator",
    "OrchestrationDetail",
    "AgentStep",
    # Solo
    "Solo",
    # Pipeline
    "Pipeline",
    "chain",
    # Router
    "Router",
    "select",
    # Parallel
    "Parallel",
    "fan_out",
    # Graph
    "Graph",
    "GraphBuilder",
    "GraphState",
    "GraphDetail",
    "Node",
    "AgentNode",
    "RouterNode",
    "FunctionNode",
    "Edge",
    "EdgeCondition",
    "NodeType",
    "create_graph",
    # Swarm
    "Swarm",
    "SwarmDetail",
    "SwarmStep",
    "Handoff",
    "swarm",
]
