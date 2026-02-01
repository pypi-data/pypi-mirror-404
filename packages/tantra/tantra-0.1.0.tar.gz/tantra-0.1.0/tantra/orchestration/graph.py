"""Graph-based Workflow Engine for Tantra.

Provides workflow orchestration with:
- Graph-based execution with conditional edges
- Cyclic workflows with termination conditions
- Mixed node types (agents, functions, routers)
- Checkpoint/resume for crash recovery and interrupts
"""

from __future__ import annotations

import asyncio
import time
import warnings
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ..agent import Agent
from ..checkpoints import Checkpoint, CheckpointStore
from ..context import ContextStore, MemoryContextStore, RunContext
from ..engine import ExecutionInterruptedError
from ..exceptions import ConfigurationError
from ..hooks import RunHooks, _invoke_hooks
from ..intheloop import InterruptResponse
from ..observability import Logger, trace_graph_run
from ..types import LogEntry, LogType, RunMetadata, RunResult, StreamEvent
from .base import Orchestrator, resolve_context, save_context


class NodeType(str, Enum):
    """Types of nodes in the graph."""

    AGENT = "agent"  # Agent node that processes input
    ROUTER = "router"  # Routes to different nodes based on condition
    BRANCH = "branch"  # Parallel branching
    JOIN = "join"  # Joins parallel branches
    START = "start"  # Entry point
    END = "end"  # Exit point


class EdgeCondition(str, Enum):
    """Predefined edge conditions."""

    ALWAYS = "always"  # Always take this edge
    ON_SUCCESS = "on_success"  # Take if previous node succeeded
    ON_FAILURE = "on_failure"  # Take if previous node failed
    ON_TOOL_CALL = "on_tool_call"  # Take if tools were called
    CUSTOM = "custom"  # Custom condition function
    CONDITIONAL = "conditional"  # Dynamic target from target_fn


@dataclass
class GraphState:
    """State that flows through the graph.

    Mutable state object that accumulates results as execution progresses.

    Attributes:
        input: Original input text to the graph.
        current_output: Most recent node output.
        history: List of dicts recording each node execution.
        metadata: Arbitrary metadata accumulated during execution.
        iteration: Current iteration counter.
        node_outputs: Mapping of node ID to its output text.
        errors: Error messages collected during execution.
        trace: Log entries from graph execution.
        run_id: Unique identifier for this graph run.
    """

    input: str
    current_output: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    node_outputs: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    trace: list[LogEntry] = field(default_factory=list)
    run_id: UUID = field(default_factory=uuid4)

    def add_result(self, node_id: str, output: str, metadata: dict | None = None) -> None:
        """Record a node's output.

        Args:
            node_id: Identifier of the node that produced the output.
            output: Output text from the node.
            metadata: Optional metadata dict to attach to the history entry.
        """
        self.node_outputs[node_id] = output
        self.current_output = output
        self.history.append(
            {
                "node_id": node_id,
                "output": output,
                "metadata": metadata or {},
                "iteration": self.iteration,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def get_output(self, node_id: str) -> str | None:
        """Get a specific node's output.

        Args:
            node_id: Identifier of the node.

        Returns:
            The node's output text, or None if the node has not executed.
        """
        return self.node_outputs.get(node_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to a serializable dictionary.

        Returns:
            Dict representation of the graph state.
        """
        return {
            "input": self.input,
            "current_output": self.current_output,
            "history": self.history,
            "metadata": self.metadata,
            "iteration": self.iteration,
            "node_outputs": self.node_outputs,
            "errors": self.errors,
            "run_id": str(self.run_id),
            "trace_count": len(self.trace),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphState:
        """Reconstruct a GraphState from a serialized dictionary.

        The ``trace`` field is not persisted; it is set to an empty list
        on reconstruction.

        Args:
            data: Dictionary previously produced by ``to_dict()``.

        Returns:
            Reconstructed GraphState instance.
        """
        return cls(
            input=data["input"],
            current_output=data.get("current_output", ""),
            history=data.get("history", []),
            metadata=data.get("metadata", {}),
            iteration=data.get("iteration", 0),
            node_outputs=data.get("node_outputs", {}),
            errors=data.get("errors", []),
            trace=[],
            run_id=UUID(data["run_id"])
            if isinstance(data.get("run_id"), str)
            else data.get("run_id", uuid4()),
        )


@dataclass
class Edge:
    """An edge connecting two nodes in the graph.

    Attributes:
        source: ID of the source node.
        target: ID of the target node (empty string for CONDITIONAL edges).
        condition: Predefined edge condition determining traversal.
        condition_fn: Custom callable for CUSTOM condition evaluation (returns bool).
        target_fn: Callable for CONDITIONAL edges that returns target node ID.
        transform_fn: Optional function to transform output before next node.
        priority: Evaluation priority. Higher values are evaluated first.
    """

    source: str
    target: str
    condition: EdgeCondition = EdgeCondition.ALWAYS
    condition_fn: Callable[[GraphState], bool] | None = None
    target_fn: Callable[[GraphState], str] | None = None
    transform_fn: Callable[[str], str] | None = None
    priority: int = 0

    def should_traverse(self, state: GraphState, success: bool, tool_called: bool) -> bool:
        """Check if this edge should be traversed.

        Args:
            state: Current graph state.
            success: Whether the source node executed successfully.
            tool_called: Whether the source node invoked a tool.

        Returns:
            True if the edge should be followed.
        """
        if self.condition == EdgeCondition.ALWAYS:
            return True
        elif self.condition == EdgeCondition.ON_SUCCESS:
            return success
        elif self.condition == EdgeCondition.ON_FAILURE:
            return not success
        elif self.condition == EdgeCondition.ON_TOOL_CALL:
            return tool_called
        elif self.condition == EdgeCondition.CUSTOM and self.condition_fn:
            return self.condition_fn(state)
        elif self.condition == EdgeCondition.CONDITIONAL and self.target_fn:
            return True
        return False

    def resolve_target(self, state: GraphState) -> str:
        """Resolve the actual target node ID.

        For CONDITIONAL edges, calls target_fn to determine the target.
        For all other edges, returns self.target.

        Args:
            state: Current graph state.

        Returns:
            Target node ID string.
        """
        if self.condition == EdgeCondition.CONDITIONAL and self.target_fn:
            return self.target_fn(state)
        return self.target


@dataclass
class Node(ABC):
    """Base class for graph nodes.

    Attributes:
        id: Unique identifier for this node.
        name: Optional human-readable name.
    """

    id: str
    name: str | None = None

    @abstractmethod
    async def execute(
        self, state: GraphState, context: RunContext | None = None
    ) -> tuple[str, bool, bool]:
        """Execute the node.

        Args:
            state: Current graph state.
            context: Optional shared RunContext passed from the graph run.

        Returns:
            Tuple of (output, success, tool_called)
        """
        pass


@dataclass
class AgentNode(Node):
    """Node that runs an agent.

    Attributes:
        agent: The Agent instance to execute, or None.
        input_transform: Optional callable to derive input from graph state.
        keep_memory: If True, preserve the agent's conversation memory
            across executions. Default is False (stateless), which clears
            memory before each run so previous node outputs don't
            accumulate as fake "user" messages.
    """

    agent: Agent | None = None
    input_transform: Callable[[GraphState], str] | None = None
    keep_memory: bool = False
    on_event: Any = None

    async def execute(
        self, state: GraphState, context: RunContext | None = None
    ) -> tuple[str, bool, bool]:
        """Execute the agent.

        Args:
            state: Current graph state.
            context: Optional shared RunContext.

        Returns:
            Tuple of (output, success, tool_called).
        """
        # Determine input
        if self.input_transform:
            input_text = self.input_transform(state)
        else:
            input_text = state.current_output or state.input

        if not self.keep_memory:
            self.agent.clear_memory()

        try:
            result = await self.agent.run(input_text, context=context, on_event=self.on_event)
            tool_called = len(result.tool_calls) > 0
            return result.output, True, tool_called
        except ExecutionInterruptedError:
            raise  # let the graph handle interrupt checkpointing
        except Exception as e:
            state.errors.append(f"Node {self.id}: {str(e)}")
            return f"Error: {str(e)}", False, False


@dataclass
class RouterNode(Node):
    """Node that routes to different targets based on conditions.

    Attributes:
        routes: Mapping of target node ID to condition callable.
        default_route: Fallback target node ID if no condition matches.
    """

    routes: dict[str, Callable[[GraphState], bool]] = field(default_factory=dict)
    default_route: str | None = None

    async def execute(
        self, state: GraphState, context: RunContext | None = None
    ) -> tuple[str, bool, bool]:
        """Determine which route to take.

        Args:
            state: Current graph state.
            context: Optional shared RunContext (unused by router).

        Returns:
            Tuple of (target_node_id, success, tool_called).
        """
        for target, condition in self.routes.items():
            if condition(state):
                return target, True, False
        if self.default_route:
            return self.default_route, True, False
        return "", False, False


@dataclass
class FunctionNode(Node):
    """Node that executes a custom function.

    Attributes:
        func: Callable that receives GraphState and returns a string
            (sync or async), or None.
    """

    func: Callable[..., str | Awaitable[str]] | None = None

    async def execute(
        self, state: GraphState, context: RunContext | None = None
    ) -> tuple[str, bool, bool]:
        """Execute the function.

        Args:
            state: Current graph state.
            context: Optional shared RunContext (unused by function nodes).

        Returns:
            Tuple of (output, success, tool_called).
        """
        try:
            result = self.func(state)
            if asyncio.iscoroutine(result):
                result = await result
            return result, True, False
        except Exception as e:
            state.errors.append(f"Node {self.id}: {str(e)}")
            return f"Error: {str(e)}", False, False


@dataclass
class GraphDetail:
    """Detail payload for graph orchestration results.

    Carried in ``RunResult.detail`` for graph-based orchestration.

    Attributes:
        state: Terminal graph state with all accumulated results.
        success: Whether execution completed without errors.
        nodes_executed: List of node IDs that were executed.
        total_iterations: Number of loop iterations performed.
        execution_path: Ordered list of node IDs visited.
    """

    state: GraphState
    success: bool
    nodes_executed: list[str]
    total_iterations: int
    execution_path: list[str]


class Graph(Orchestrator):
    """Graph-based orchestration for multi-agent workflows.

    Examples:
        ```python
        # Create a simple graph
        graph = Graph()

        # Add nodes
        graph.add_node(AgentNode("researcher", agent=researcher_agent))
        graph.add_node(AgentNode("writer", agent=writer_agent))
        graph.add_node(AgentNode("editor", agent=editor_agent))

        # Add edges
        graph.add_edge("START", "researcher")
        graph.add_edge("researcher", "writer")
        graph.add_edge("writer", "editor")
        graph.add_edge("editor", "END")

        # Execute
        result = await graph.run("Write about AI")
        ```
    """

    def __init__(
        self,
        name: str = "graph",
        max_iterations: int = 50,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ):
        """Initialize graph.

        Args:
            name: Human-readable name for this graph.
            max_iterations: Maximum execution loop iterations before stopping.
            context_store: Optional store for persisting shared context.
            hooks: Optional list of RunHooks for lifecycle notifications.
            checkpoint_store: Optional store for inter-node checkpointing.
                When provided, a checkpoint is saved after each node completes,
                enabling crash recovery via ``resume()``.
        """
        self._name = name
        self.max_iterations = max_iterations
        self._context_store: ContextStore = context_store or MemoryContextStore()
        self._hooks: list[RunHooks] = hooks or []
        self._checkpoint_store: CheckpointStore | None = checkpoint_store
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []
        self._start_node: str | None = None
        self._end_nodes: set[str] = set()

    @property
    def orchestration_type(self) -> str:
        """The type of orchestration pattern."""
        return "graph"

    def clone(self, **kwargs: Any) -> Graph:
        """Create a copy of this graph with optional resource overrides.

        Shares the graph topology (nodes, edges) by reference.
        Accepts session-scoped ``checkpoint_store`` and ``context_store``.

        Args:
            **kwargs: Optional overrides. Recognised keys:
                ``checkpoint_store`` — session-scoped checkpoint store.
                ``context_store`` — session-scoped context store.

        Returns:
            A new Graph with the same topology and configuration.
        """
        g = Graph(
            name=self._name,
            max_iterations=self.max_iterations,
            context_store=kwargs.get("context_store", self._context_store),
            hooks=self._hooks,
            checkpoint_store=kwargs.get("checkpoint_store", self._checkpoint_store),
        )
        g._nodes = self._nodes
        g._edges = self._edges
        g._start_node = self._start_node
        g._end_nodes = self._end_nodes
        return g

    def add_node(self, node: Node) -> Graph:
        """Add a node to the graph.

        Args:
            node: Node instance to add.

        Returns:
            Self for method chaining.
        """
        self._nodes[node.id] = node
        return self

    def add_agent(
        self,
        node_id: str,
        agent: Agent,
        input_transform: Callable[[GraphState], str] | None = None,
        keep_memory: bool = False,
    ) -> Graph:
        """Convenience method to add an agent node.

        Args:
            node_id: Unique identifier for the node.
            agent: Agent instance to associate with the node.
            input_transform: Optional callable to derive input from graph state.
            keep_memory: If True, preserve the agent's conversation memory
                across executions instead of clearing it each time.

        Returns:
            Self for method chaining.
        """
        node = AgentNode(
            id=node_id,
            name=node_id,
            agent=agent,
            input_transform=input_transform,
            keep_memory=keep_memory,
        )
        return self.add_node(node)

    def add_router(
        self,
        node_id: str,
        routes: dict[str, Callable[[GraphState], bool]],
        default: str | None = None,
    ) -> Graph:
        """Add a router node.

        Args:
            node_id: Unique identifier for the router node.
            routes: Mapping of target node ID to condition callable.
            default: Fallback target node ID if no route matches.

        Returns:
            Self for method chaining.
        """
        node = RouterNode(
            id=node_id,
            name=node_id,
            routes=routes,
            default_route=default,
        )
        return self.add_node(node)

    def add_function(
        self,
        node_id: str,
        func: Callable[[GraphState], str | Awaitable[str]],
    ) -> Graph:
        """Add a function node.

        Args:
            node_id: Unique identifier for the function node.
            func: Callable that receives GraphState and returns a string.

        Returns:
            Self for method chaining.
        """
        node = FunctionNode(id=node_id, name=node_id, func=func)
        return self.add_node(node)

    def add_edge(
        self,
        source: str,
        target: str,
        condition: EdgeCondition = EdgeCondition.ALWAYS,
        condition_fn: Callable[[GraphState], bool] | None = None,
        transform_fn: Callable[[str], str] | None = None,
        priority: int = 0,
    ) -> Graph:
        """Add an edge between nodes.

        Args:
            source: Source node ID (or "START" for entry).
            target: Target node ID (or "END" for exit).
            condition: Predefined condition for edge traversal.
            condition_fn: Custom callable for CUSTOM condition evaluation.
            transform_fn: Optional function to transform output before next node.
            priority: Edge evaluation priority. Higher values are evaluated first.
                Edges with equal priority preserve insertion order.

        Returns:
            Self for method chaining.
        """
        edge = Edge(
            source=source,
            target=target,
            condition=condition,
            condition_fn=condition_fn,
            transform_fn=transform_fn,
            priority=priority,
        )
        self._edges.append(edge)

        # Track start and end
        if source == "START":
            self._start_node = target
        if target == "END":
            self._end_nodes.add(source)

        return self

    def add_conditional_edge(
        self,
        source: str,
        condition_fn: Callable[[GraphState], str],
    ) -> Graph:
        """Add a conditional edge with dynamic target resolution.

        The condition_fn receives the current GraphState and must return
        the ID of the next node to execute (or "END" to finish).

        Args:
            source: Source node ID.
            condition_fn: Callable that receives GraphState and returns target node ID.

        Returns:
            Self for method chaining.
        """
        edge = Edge(
            source=source,
            target="",
            condition=EdgeCondition.CONDITIONAL,
            target_fn=condition_fn,
        )
        self._edges.append(edge)
        return self

    def set_entry_point(self, node_id: str) -> Graph:
        """Set the entry point node.

        Args:
            node_id: ID of the node to use as the graph entry point.

        Returns:
            Self for method chaining.
        """
        self._start_node = node_id
        return self

    def set_finish_point(self, node_id: str) -> Graph:
        """Mark a node as a finish point.

        Args:
            node_id: ID of the node to mark as a graph exit point.

        Returns:
            Self for method chaining.
        """
        self._end_nodes.add(node_id)
        return self

    def validate(self) -> list[str]:
        """Validate the graph structure and return a list of errors.

        Checks for:
        - No start node defined
        - Start node not a registered node
        - Edge sources referencing non-existent nodes (ignoring "START")
        - Edge targets referencing non-existent nodes (ignoring "END"),
          skipping CONDITIONAL edges whose targets are resolved dynamically
        - CUSTOM edges missing condition_fn
        - CONDITIONAL edges missing target_fn
        - Non-end nodes with no outgoing edges

        Returns:
            List of error message strings. Empty list means the graph is valid.
        """
        errors: list[str] = []
        valid_sources = set(self._nodes.keys()) | {"START"}
        valid_targets = set(self._nodes.keys()) | {"END"}

        if not self._start_node:
            errors.append("No start node defined. Use set_entry_point() or add_edge('START', ...).")

        if self._start_node and self._start_node not in self._nodes:
            errors.append(f"Start node '{self._start_node}' is not a registered node.")

        for edge in self._edges:
            if edge.source not in valid_sources:
                errors.append(f"Edge source '{edge.source}' is not a registered node or 'START'.")
            if edge.condition != EdgeCondition.CONDITIONAL and edge.target not in valid_targets:
                errors.append(f"Edge target '{edge.target}' is not a registered node or 'END'.")
            if edge.condition == EdgeCondition.CUSTOM and edge.condition_fn is None:
                errors.append(
                    f"Edge from '{edge.source}' to '{edge.target}' has CUSTOM condition "
                    f"but no condition_fn."
                )
            if edge.condition == EdgeCondition.CONDITIONAL and edge.target_fn is None:
                errors.append(
                    f"Edge from '{edge.source}' has CONDITIONAL condition " f"but no target_fn."
                )

        for node_id, node in self._nodes.items():
            if node_id in self._end_nodes:
                continue
            # RouterNodes handle routing internally via their routes dict
            if isinstance(node, RouterNode):
                continue
            outgoing = [e for e in self._edges if e.source == node_id]
            if not outgoing:
                errors.append(f"Node '{node_id}' has no outgoing edges and is not an end node.")

        return errors

    def _get_outgoing_edges(self, node_id: str) -> list[Edge]:
        """Get all outgoing edges from a node, sorted by priority (highest first)."""
        edges = [e for e in self._edges if e.source == node_id]
        edges.sort(key=lambda e: e.priority, reverse=True)
        return edges

    def _get_next_node(
        self,
        current_node: str,
        state: GraphState,
        success: bool,
        tool_called: bool,
    ) -> tuple[str | None, Edge | None]:
        """Determine the next node to execute.

        Returns:
            Tuple of (target_node_id, matched_edge). Both are None if no
            matching edge is found.
        """
        edges = self._get_outgoing_edges(current_node)

        for edge in edges:
            if edge.should_traverse(state, success, tool_called):
                return edge.resolve_target(state), edge

        return None, None

    async def _save_graph_checkpoint(
        self,
        *,
        state: GraphState,
        ctx: RunContext | None,
        next_node: str | None,
        nodes_executed: list[str],
        execution_path: list[str],
        iteration: int,
        graph_run_id: UUID,
        session_id: str | None,
        checkpoint_type: str = "graph_progress",
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Save a graph checkpoint after a node completes or an interrupt occurs.

        Args:
            state: Current graph state.
            ctx: Shared RunContext, or None.
            next_node: The node to execute next on resume. ``None`` for
                interrupt checkpoints (use ``interrupted_node_id`` in
                *extra_context* instead).
            nodes_executed: Nodes executed so far.
            execution_path: Full execution path so far.
            iteration: Current iteration counter.
            graph_run_id: Run ID for this graph execution.
            session_id: Optional session ID for grouping checkpoints.
            checkpoint_type: Type of checkpoint (``"graph_progress"`` or
                ``"graph_interrupt"``).
            extra_context: Additional context fields merged into the
                checkpoint context dict (e.g. ``agent_checkpoint_id``).

        Returns:
            The saved checkpoint ID.
        """
        context_data: dict[str, Any] = {
            "graph_state": state.to_dict(),
            "context_data": ctx.to_dict() if ctx else None,
            "nodes_executed": list(nodes_executed),
            "execution_path": list(execution_path),
            "iteration": iteration,
            "graph_name": self.name,
        }
        if next_node is not None:
            context_data["next_node"] = next_node
        if extra_context:
            context_data.update(extra_context)

        checkpoint = Checkpoint(
            name=self.name,
            run_id=graph_run_id,
            session_id=session_id,
            checkpoint_type=checkpoint_type,
            messages=[],
            context=context_data,
            status="pending",
        )
        return await self._checkpoint_store.save(checkpoint)

    async def _handle_node_interrupt(
        self,
        error: ExecutionInterruptedError,
        *,
        current_node: str,
        state: GraphState,
        ctx: RunContext | None,
        nodes_executed: list[str],
        execution_path: list[str],
        iteration: int,
        graph_run_id: UUID,
        session_id: str | None,
    ) -> None:
        """Handle an ``ExecutionInterruptedError`` from a node.

        If a checkpoint store is configured, saves a ``graph_interrupt``
        checkpoint and re-raises with the graph-level checkpoint ID.
        Otherwise re-raises the original error unchanged.

        This method always raises and never returns normally.

        Args:
            error: The interrupt error from the agent node.
            current_node: ID of the interrupted node.
            state: Current graph state.
            ctx: Shared RunContext, or None.
            nodes_executed: Nodes executed so far.
            execution_path: Full execution path so far.
            iteration: Current iteration counter.
            graph_run_id: Run ID for this graph execution.
            session_id: Optional session ID for grouping checkpoints.

        Raises:
            ExecutionInterruptedError: Always — with graph checkpoint ID
                if a store is available, or the original agent checkpoint ID.
        """
        if self._checkpoint_store is not None:
            graph_cp_id = await self._save_graph_checkpoint(
                state=state,
                ctx=ctx,
                next_node=None,
                nodes_executed=nodes_executed,
                execution_path=execution_path,
                iteration=iteration,
                graph_run_id=graph_run_id,
                session_id=session_id,
                checkpoint_type="graph_interrupt",
                extra_context={
                    "agent_checkpoint_id": error.checkpoint_id,
                    "interrupted_node_id": current_node,
                },
            )
            raise ExecutionInterruptedError(graph_cp_id, error.prompt) from error
        raise error

    def _has_interrupt_agents(self) -> bool:
        """Check if any agent node has interrupt-capable tools."""
        for node in self._nodes.values():
            if isinstance(node, AgentNode) and node.agent and node.agent._tools:
                for tool_def in node.agent._tools:
                    if tool_def.requires_interrupt:
                        return True
        return False

    async def _execute_loop(
        self,
        *,
        state: GraphState,
        ctx: RunContext | None,
        start_node: str,
        start_iteration: int,
        nodes_executed: list[str],
        execution_path: list[str],
        graph_run_id: UUID,
        session_id: str | None,
        logger: Logger,
    ) -> RunResult[GraphDetail]:
        """Core execution loop shared by ``run()`` and ``resume()``.

        Args:
            state: Mutable graph state.
            ctx: Shared RunContext, or None.
            start_node: Node ID to begin execution at.
            start_iteration: Iteration counter to start from.
            nodes_executed: Mutable list of executed node IDs.
            execution_path: Mutable list of visited node IDs.
            graph_run_id: Run ID for tracing.
            session_id: Optional session ID for checkpointing.
            logger: Logger instance for this run.

        Returns:
            RunResult[GraphDetail] with final output and execution details.
        """
        current_node = start_node
        iteration = start_iteration
        last_checkpoint_id: str | None = None

        while iteration < self.max_iterations:
            state.iteration = iteration

            # Check if we've reached an end
            if current_node == "END" or current_node in self._end_nodes:
                if current_node != "END":
                    # Execute the end node first
                    node = self._nodes.get(current_node)
                    if node:
                        if isinstance(node, AgentNode):
                            node.on_event = self._active_on_event
                        await self._emit_step(StreamEvent("node_start", {
                            "node": current_node, "iteration": iteration,
                        }))
                        node_start = time.time()
                        try:
                            output, success, tool_called = await node.execute(
                                state, context=ctx,
                            )
                        except ExecutionInterruptedError as e:
                            execution_path.append(current_node)
                            await self._handle_node_interrupt(
                                e,
                                current_node=current_node,
                                state=state,
                                ctx=ctx,
                                nodes_executed=nodes_executed,
                                execution_path=execution_path,
                                iteration=iteration,
                                graph_run_id=graph_run_id,
                                session_id=session_id,
                            )
                        duration_ms = (time.time() - node_start) * 1000
                        state.add_result(current_node, output)
                        nodes_executed.append(current_node)
                        execution_path.append(current_node)
                        # Log end node execution
                        logger.log(
                            LogType.TOOL_RESULT,
                            data={
                                "node_id": current_node,
                                "output": output[:500],
                                "success": success,
                                "is_end_node": True,
                            },
                            metadata={"duration_ms": duration_ms, "iteration": iteration},
                        )
                        await self._emit_step(StreamEvent("node_complete", {
                            "node": current_node, "output": output[:500],
                            "duration_ms": duration_ms, "next_node": "END",
                        }))
                        # Save checkpoint for end node
                        if self._checkpoint_store is not None:
                            last_checkpoint_id = await self._save_graph_checkpoint(
                                state=state,
                                ctx=ctx,
                                next_node="END",
                                nodes_executed=nodes_executed,
                                execution_path=execution_path,
                                iteration=iteration,
                                graph_run_id=graph_run_id,
                                session_id=session_id,
                            )
                break

            # Get the node
            node = self._nodes.get(current_node)
            if not node:
                state.errors.append(f"Node not found: {current_node}")
                logger.log_error(
                    ValueError(f"Node not found: {current_node}"), context="graph_execution"
                )
                break

            # Execute the node
            execution_path.append(current_node)

            # Log node execution start
            logger.log(
                LogType.TOOL_CALL,
                data={
                    "node_id": current_node,
                    "node_type": type(node).__name__,
                    "iteration": iteration,
                },
            )

            if isinstance(node, AgentNode):
                node.on_event = self._active_on_event

            await self._emit_step(StreamEvent("node_start", {
                "node": current_node, "iteration": iteration,
            }))

            node_start = time.time()

            if isinstance(node, RouterNode):
                # Router returns the next node ID
                next_node_id, success, _ = await node.execute(state, context=ctx)
                duration_ms = (time.time() - node_start) * 1000

                # Record the router's decision in state
                state.add_result(current_node, next_node_id)
                nodes_executed.append(current_node)

                logger.log(
                    LogType.TOOL_RESULT,
                    data={"node_id": current_node, "routed_to": next_node_id, "success": success},
                    metadata={"duration_ms": duration_ms, "iteration": iteration},
                )
                await self._emit_step(StreamEvent("node_complete", {
                    "node": current_node, "output": next_node_id,
                    "duration_ms": duration_ms, "next_node": next_node_id if success else None,
                }))
                if success and next_node_id:
                    # Save checkpoint after router decision
                    if self._checkpoint_store is not None:
                        last_checkpoint_id = await self._save_graph_checkpoint(
                            state=state,
                            ctx=ctx,
                            next_node=next_node_id,
                            nodes_executed=nodes_executed,
                            execution_path=execution_path,
                            iteration=iteration,
                            graph_run_id=graph_run_id,
                            session_id=session_id,
                        )
                    current_node = next_node_id
                else:
                    break
            else:
                # Regular node execution
                try:
                    output, success, tool_called = await node.execute(state, context=ctx)
                except ExecutionInterruptedError as e:
                    await self._handle_node_interrupt(
                        e,
                        current_node=current_node,
                        state=state,
                        ctx=ctx,
                        nodes_executed=nodes_executed,
                        execution_path=execution_path,
                        iteration=iteration,
                        graph_run_id=graph_run_id,
                        session_id=session_id,
                    )

                duration_ms = (time.time() - node_start) * 1000
                state.add_result(current_node, output)
                nodes_executed.append(current_node)

                # Log node result
                logger.log(
                    LogType.TOOL_RESULT,
                    data={
                        "node_id": current_node,
                        "output": output[:500],
                        "success": success,
                        "tool_called": tool_called,
                    },
                    metadata={"duration_ms": duration_ms, "iteration": iteration},
                )

                # Determine next node
                next_node, matched_edge = self._get_next_node(
                    current_node, state, success, tool_called
                )

                # Apply edge transform if present
                if matched_edge and matched_edge.transform_fn and state.current_output:
                    state.current_output = matched_edge.transform_fn(state.current_output)

                await self._emit_step(StreamEvent("node_complete", {
                    "node": current_node, "output": output[:500],
                    "duration_ms": duration_ms, "next_node": next_node or "END",
                }))

                if next_node is None or next_node == "END":
                    # Save final checkpoint before breaking
                    if self._checkpoint_store is not None:
                        last_checkpoint_id = await self._save_graph_checkpoint(
                            state=state,
                            ctx=ctx,
                            next_node=next_node or "END",
                            nodes_executed=nodes_executed,
                            execution_path=execution_path,
                            iteration=iteration,
                            graph_run_id=graph_run_id,
                            session_id=session_id,
                        )
                    break

                # Save checkpoint after node completes, recording the next node
                if self._checkpoint_store is not None:
                    last_checkpoint_id = await self._save_graph_checkpoint(
                        state=state,
                        ctx=ctx,
                        next_node=next_node,
                        nodes_executed=nodes_executed,
                        execution_path=execution_path,
                        iteration=iteration,
                        graph_run_id=graph_run_id,
                        session_id=session_id,
                    )
                current_node = next_node

            iteration += 1

        # Mark the last checkpoint as completed
        if self._checkpoint_store is not None and last_checkpoint_id is not None:
            await self._checkpoint_store.update(last_checkpoint_id, status="completed")

        # Log graph completion
        logger.log(
            LogType.FINAL_RESPONSE,
            data={
                "output": state.current_output[:500],
                "nodes_executed": nodes_executed,
                "execution_path": execution_path,
            },
            metadata={"total_iterations": iteration, "duration_ms": logger.get_duration_ms()},
        )

        # Store trace in state
        state.trace = logger.entries

        return RunResult(
            output=state.current_output,
            trace=logger.entries,
            metadata=RunMetadata(
                run_id=graph_run_id,
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                estimated_cost=0,
                duration_ms=logger.get_duration_ms(),
                tool_calls_count=0,
            ),
            detail=GraphDetail(
                state=state,
                success=len(state.errors) == 0,
                nodes_executed=nodes_executed,
                total_iterations=iteration,
                execution_path=execution_path,
            ),
            context=ctx,
        )

    @trace_graph_run
    async def run(
        self,
        input_text: str,
        run_id: UUID | None = None,
        shared_context: RunContext | None = None,
        session_id: str | None = None,
    ) -> RunResult[GraphDetail]:
        """Execute the graph.

        Args:
            input_text: Initial input to the graph.
            run_id: Optional run ID for tracing.
            shared_context: Optional RunContext shared across all agent nodes.
            session_id: Optional session ID for persisting shared context across runs.

        Returns:
            RunResult[GraphDetail] with final output and execution details.

        Raises:
            ValueError: If no start node has been defined.
        """
        if not self._start_node:
            raise ValueError(
                "No start node defined. Use set_entry_point() or add_edge('START', ...)"
            )

        # Validate graph structure
        validation_errors = self.validate()
        if validation_errors:
            raise ConfigurationError(
                f"Graph '{self.name}' has validation errors:\n"
                + "\n".join(f"  - {e}" for e in validation_errors)
            )

        # Warn if agents have interrupt tools but graph has no checkpoint store
        if self._checkpoint_store is None and self._has_interrupt_agents():
            warnings.warn(
                f"Graph '{self.name}' contains agent nodes with interrupt tools but "
                f"no checkpoint_store is configured. If an interrupt fires, the graph "
                f"state will not be saved and only the agent-level checkpoint ID will "
                f"be available — graph.resume() will not work. Pass checkpoint_store "
                f"to Graph() to enable graph-level interrupt recovery.",
                UserWarning,
                stacklevel=2,
            )

        graph_run_id = run_id or uuid4()
        ctx = await resolve_context(self._context_store, shared_context, session_id)

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_start",
                run_id=graph_run_id,
                user_input=input_text,
                orchestration_type="graph",
                context=ctx,
            )

        logger = Logger(run_id=graph_run_id)
        logger.start_run()

        state = GraphState(input=input_text, current_output=input_text, run_id=graph_run_id)
        nodes_executed: list[str] = []
        execution_path: list[str] = []

        # Log graph start
        logger.log(
            LogType.PROMPT,
            data={"graph_name": self.name, "input": input_text, "start_node": self._start_node},
            metadata={"graph_execution": True},
        )

        orch_result = await self._execute_loop(
            state=state,
            ctx=ctx,
            start_node=self._start_node,
            start_iteration=0,
            nodes_executed=nodes_executed,
            execution_path=execution_path,
            graph_run_id=graph_run_id,
            session_id=session_id,
            logger=logger,
        )

        await save_context(self._context_store, ctx, session_id)

        if self._hooks:
            await _invoke_hooks(
                self._hooks,
                "on_orchestration_end",
                run_id=graph_run_id,
                result=orch_result,
                orchestration_type="graph",
                context=ctx,
            )

        return orch_result

    async def resume(
        self,
        checkpoint_id: str,
        checkpoint_store: CheckpointStore | None = None,
        response: InterruptResponse | None = None,
    ) -> RunResult[GraphDetail]:
        """Resume graph execution from a checkpoint.

        Supports two checkpoint types:

        - ``"graph_progress"`` — crash recovery. Resumes from the next
          unexecuted node. No ``response`` needed.
        - ``"graph_interrupt"`` — an agent node's tool triggered a
          human-in-the-loop interrupt. Supply a ``response`` to answer
          the interrupt, resume the agent, then continue the graph.

        Args:
            checkpoint_id: ID of the checkpoint to resume from.
            checkpoint_store: Optional store override; falls back to
                ``self._checkpoint_store``.
            response: Required for ``"graph_interrupt"`` checkpoints.
                The human's response to the interrupted tool.

        Returns:
            RunResult[GraphDetail] with final output and execution details.

        Raises:
            ConfigurationError: If no checkpoint store is available.
            ValueError: If the checkpoint is not found, has wrong type,
                or ``response`` is missing for an interrupt checkpoint.
        """
        store = checkpoint_store or self._checkpoint_store
        if store is None:
            raise ConfigurationError(
                "No checkpoint store available. Pass checkpoint_store to Graph() or resume()."
            )

        checkpoint = await store.load(checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        if checkpoint.checkpoint_type == "graph_interrupt":
            return await self._resume_interrupt(checkpoint, store, response)
        elif checkpoint.checkpoint_type == "graph_progress":
            return await self._resume_progress(checkpoint, store)
        else:
            raise ValueError(
                f"Expected checkpoint_type 'graph_progress' or 'graph_interrupt', "
                f"got '{checkpoint.checkpoint_type}'"
            )

    async def _resume_progress(
        self,
        checkpoint: Checkpoint,
        store: CheckpointStore,
    ) -> RunResult[GraphDetail]:
        """Resume from a ``graph_progress`` checkpoint (crash recovery).

        Args:
            checkpoint: The loaded checkpoint.
            store: The checkpoint store used for loading.

        Returns:
            RunResult[GraphDetail] from the continued execution.
        """
        ctx_data = checkpoint.context
        graph_state_data = ctx_data["graph_state"]
        context_data = ctx_data.get("context_data")
        next_node = ctx_data["next_node"]
        nodes_executed = list(ctx_data.get("nodes_executed", []))
        execution_path = list(ctx_data.get("execution_path", []))
        iteration = ctx_data.get("iteration", 0)

        state = GraphState.from_dict(graph_state_data)
        ctx = RunContext(context_data) if context_data else None

        await store.update(checkpoint.id, status="completed")

        graph_run_id = state.run_id
        logger = Logger(run_id=graph_run_id)
        logger.start_run()

        logger.log(
            LogType.PROMPT,
            data={
                "graph_name": self.name,
                "resumed_from": checkpoint.id,
                "next_node": next_node,
                "nodes_already_executed": nodes_executed,
            },
            metadata={"graph_resume": True},
        )

        return await self._execute_loop(
            state=state,
            ctx=ctx,
            start_node=next_node,
            start_iteration=iteration + 1,
            nodes_executed=nodes_executed,
            execution_path=execution_path,
            graph_run_id=graph_run_id,
            session_id=checkpoint.session_id,
            logger=logger,
        )

    async def _resume_interrupt(
        self,
        checkpoint: Checkpoint,
        store: CheckpointStore,
        response: InterruptResponse | None,
    ) -> RunResult[GraphDetail]:
        """Resume from a ``graph_interrupt`` checkpoint (human-in-the-loop).

        Resumes the interrupted agent, records its output in graph state,
        then continues the graph from the next node.

        Args:
            checkpoint: The loaded checkpoint.
            store: The checkpoint store used for loading.
            response: The human's response. Required.

        Returns:
            RunResult[GraphDetail] from the continued execution.

        Raises:
            ValueError: If *response* is None, the interrupted node is
                not an AgentNode, or the agent's checkpoint store is
                inaccessible.
        """
        if response is None:
            raise ValueError("InterruptResponse required to resume a 'graph_interrupt' checkpoint.")

        ctx_data = checkpoint.context
        graph_state_data = ctx_data["graph_state"]
        context_data = ctx_data.get("context_data")
        agent_checkpoint_id = ctx_data["agent_checkpoint_id"]
        interrupted_node_id = ctx_data["interrupted_node_id"]
        nodes_executed = list(ctx_data.get("nodes_executed", []))
        execution_path = list(ctx_data.get("execution_path", []))
        iteration = ctx_data.get("iteration", 0)

        node = self._nodes.get(interrupted_node_id)
        if not isinstance(node, AgentNode):
            raise ValueError(f"Interrupted node '{interrupted_node_id}' is not an AgentNode.")

        # Verify the agent can actually resume (has a checkpoint store)
        if node.agent.checkpoint_store is None:
            raise ConfigurationError(
                f"Agent in node '{interrupted_node_id}' has no checkpoint_store. "
                f"Cannot resume from an interrupt without an agent-level store."
            )

        state = GraphState.from_dict(graph_state_data)
        ctx = RunContext(context_data) if context_data else None

        await store.update(checkpoint.id, status="completed")

        graph_run_id = state.run_id
        logger = Logger(run_id=graph_run_id)
        logger.start_run()

        logger.log(
            LogType.PROMPT,
            data={
                "graph_name": self.name,
                "resumed_from": checkpoint.id,
                "interrupted_node": interrupted_node_id,
                "agent_checkpoint_id": agent_checkpoint_id,
            },
            metadata={"graph_interrupt_resume": True},
        )

        # Resume the agent — executes the pending tool and continues
        # the agent's internal loop until it finishes.
        agent_result = await node.agent.resume(agent_checkpoint_id, response)

        # Record the agent result as if the node completed normally
        state.add_result(interrupted_node_id, agent_result.output)
        nodes_executed.append(interrupted_node_id)
        execution_path.append(interrupted_node_id)

        tool_called = len(agent_result.tool_calls) > 0
        next_node, matched_edge = self._get_next_node(
            interrupted_node_id, state, success=True, tool_called=tool_called
        )

        # Apply edge transform if present
        if matched_edge and matched_edge.transform_fn and state.current_output:
            state.current_output = matched_edge.transform_fn(state.current_output)

        if next_node is None or next_node == "END":
            # Graph is done — build final result
            logger.log(
                LogType.FINAL_RESPONSE,
                data={
                    "output": state.current_output[:500],
                    "nodes_executed": nodes_executed,
                    "execution_path": execution_path,
                },
                metadata={
                    "total_iterations": iteration,
                    "duration_ms": logger.get_duration_ms(),
                },
            )
            state.trace = logger.entries
            return RunResult(
                output=state.current_output,
                trace=logger.entries,
                metadata=RunMetadata(
                    run_id=graph_run_id,
                    total_tokens=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    estimated_cost=0,
                    duration_ms=logger.get_duration_ms(),
                    tool_calls_count=0,
                ),
                detail=GraphDetail(
                    state=state,
                    success=len(state.errors) == 0,
                    nodes_executed=nodes_executed,
                    total_iterations=iteration,
                    execution_path=execution_path,
                ),
                context=ctx,
            )

        # Continue the graph from the next node
        return await self._execute_loop(
            state=state,
            ctx=ctx,
            start_node=next_node,
            start_iteration=iteration + 1,
            nodes_executed=nodes_executed,
            execution_path=execution_path,
            graph_run_id=graph_run_id,
            session_id=checkpoint.session_id,
            logger=logger,
        )


# =============================================================================
# Graph Builder (Fluent API)
# =============================================================================


class GraphBuilder:
    """Fluent builder for creating graphs.

    Examples:
        ```python
        graph = (
            GraphBuilder("content_pipeline")
            .add_agent("research", researcher)
            .add_agent("write", writer)
            .add_agent("edit", editor)
            .edge("START", "research")
            .edge("research", "write")
            .edge("write", "edit")
            .edge("edit", "END")
            .build()
        )
        ```
    """

    def __init__(
        self,
        name: str = "graph",
        max_iterations: int = 50,
        context_store: ContextStore | None = None,
        hooks: list[RunHooks] | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ):
        """Initialize GraphBuilder.

        Args:
            name: Human-readable name for the graph.
            max_iterations: Maximum execution loop iterations.
            context_store: Optional store for persisting shared context.
            hooks: Optional list of RunHooks for lifecycle notifications.
            checkpoint_store: Optional store for inter-node checkpointing.
        """
        self._graph = Graph(
            name=name,
            max_iterations=max_iterations,
            context_store=context_store,
            hooks=hooks,
            checkpoint_store=checkpoint_store,
        )

    def add_agent(
        self,
        node_id: str,
        agent: Agent,
        input_transform: Callable[[GraphState], str] | None = None,
        keep_memory: bool = False,
    ) -> GraphBuilder:
        """Add an agent node.

        Args:
            node_id: Unique identifier for the node.
            agent: Agent instance to associate with the node.
            input_transform: Optional callable to derive input from graph state.
            keep_memory: If True, preserve the agent's conversation memory
                across executions instead of clearing it each time.

        Returns:
            Self for method chaining.
        """
        self._graph.add_agent(node_id, agent, input_transform, keep_memory)
        return self

    def add_router(
        self,
        node_id: str,
        routes: dict[str, Callable[[GraphState], bool]],
        default: str | None = None,
    ) -> GraphBuilder:
        """Add a router node.

        Args:
            node_id: Unique identifier for the router node.
            routes: Mapping of target node ID to condition callable.
            default: Fallback target node ID if no route matches.

        Returns:
            Self for method chaining.
        """
        self._graph.add_router(node_id, routes, default)
        return self

    def add_function(
        self,
        node_id: str,
        func: Callable[[GraphState], str | Awaitable[str]],
    ) -> GraphBuilder:
        """Add a function node.

        Args:
            node_id: Unique identifier for the function node.
            func: Callable that receives GraphState and returns a string.

        Returns:
            Self for method chaining.
        """
        self._graph.add_function(node_id, func)
        return self

    def edge(
        self,
        source: str,
        target: str,
        condition: EdgeCondition = EdgeCondition.ALWAYS,
        condition_fn: Callable[[GraphState], bool] | None = None,
        priority: int = 0,
    ) -> GraphBuilder:
        """Add an edge.

        Args:
            source: Source node ID (or "START").
            target: Target node ID (or "END").
            condition: Predefined condition for edge traversal.
            condition_fn: Custom callable for CUSTOM condition evaluation.
            priority: Edge evaluation priority. Higher values are evaluated first.

        Returns:
            Self for method chaining.
        """
        self._graph.add_edge(source, target, condition, condition_fn, priority=priority)
        return self

    def conditional_edge(
        self,
        source: str,
        condition_fn: Callable[[GraphState], str],
    ) -> GraphBuilder:
        """Add a conditional edge that dynamically selects the target node.

        The condition_fn receives the current GraphState and must return
        the ID of the next node to execute (or "END" to finish).

        Args:
            source: Source node ID.
            condition_fn: Callable that receives GraphState and returns target node ID.

        Returns:
            Self for method chaining.
        """
        self._graph.add_conditional_edge(source, condition_fn)
        return self

    def build(self) -> Graph:
        """Build and return the graph.

        Returns:
            Configured Graph instance.

        Raises:
            ConfigurationError: If the graph has structural errors.
        """
        validation_errors = self._graph.validate()
        if validation_errors:
            raise ConfigurationError(
                f"Graph '{self._graph.name}' has validation errors:\n"
                + "\n".join(f"  - {e}" for e in validation_errors)
            )
        return self._graph


# =============================================================================
# Convenience Functions
# =============================================================================


def create_graph(
    name: str = "graph",
    max_iterations: int = 50,
    context_store: ContextStore | None = None,
    checkpoint_store: CheckpointStore | None = None,
) -> GraphBuilder:
    """Create a new graph builder.

    Args:
        name: Human-readable name for the graph.
        max_iterations: Maximum execution loop iterations.
        context_store: Optional store for persisting shared context.
        checkpoint_store: Optional store for inter-node checkpointing.

    Returns:
        GraphBuilder for fluent graph construction.

    Examples:
        ```python
        graph = (
            create_graph("my_workflow")
            .add_agent("agent1", agent1)
            .add_agent("agent2", agent2)
            .edge("START", "agent1")
            .edge("agent1", "agent2")
            .edge("agent2", "END")
            .build()
        )
        ```
    """
    return GraphBuilder(
        name, max_iterations, context_store=context_store, checkpoint_store=checkpoint_store
    )
