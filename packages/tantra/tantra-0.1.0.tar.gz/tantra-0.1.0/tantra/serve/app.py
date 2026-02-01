"""RunnableServer and serve() for exposing Tantra orchestrators over HTTP.

Provides a FastAPI-based HTTP server with run execution, interrupt/resume,
checkpoint inspection, and SSE streaming.

Quick start::

    from tantra import Agent
    from tantra.serve import serve

    agent = Agent("openai:gpt-4o", system_prompt="You are helpful.")
    app = serve(agent)

    if __name__ == "__main__":
        serve(agent, run=True)
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ..agent import Agent
from ..engine import ExecutionInterruptedError
from ..exceptions import ConfigurationError
from ..intheloop import InterruptResponse
from ..orchestration.base import OrchestrationDetail, Orchestrator
from ..orchestration.graph import GraphDetail
from ..orchestration.solo import Solo
from ..orchestration.swarm import SwarmDetail
from .factory import PostgresRunnableFactory, RunnableFactory
from .models import (
    CheckpointSummary,
    HealthResponse,
    ResumeRequest,
    RunnableInfo,
    RunRequest,
    RunResponse,
)


def _serialize_detail(detail: Any) -> dict[str, Any] | None:
    """Serialize orchestration detail to a JSON-safe dict.

    Args:
        detail: A detail object from RunResult (GraphDetail, SwarmDetail, etc.)
            or None.

    Returns:
        Serialized dict, or None if detail is None or unrecognised.
    """
    if detail is None:
        return None
    if isinstance(detail, GraphDetail):
        return {
            "type": "graph",
            "success": detail.success,
            "nodes_executed": detail.nodes_executed,
            "execution_path": detail.execution_path,
            "total_iterations": detail.total_iterations,
            "node_outputs": detail.state.node_outputs,
        }
    if isinstance(detail, SwarmDetail):
        return {
            "type": "swarm",
            "handoff_chain": detail.handoff_chain,
            "handoff_count": detail.handoff_count,
            "steps": [
                {
                    "agent_id": s.agent_id,
                    "output": s.output[:500],
                    "handoff_to": s.handoff_to,
                }
                for s in detail.steps
            ],
        }
    if isinstance(detail, OrchestrationDetail):
        return {
            "type": detail.orchestration_type,
            "steps": [
                {"agent_id": s.agent_id, "output": s.output[:500]}
                for s in detail.steps
            ],
        }
    return None


class RunnableServer:
    """HTTP server that wraps one or more Tantra orchestrators.

    Manages session isolation via a RunnableFactory and exposes
    run, resume, checkpoint, and SSE streaming endpoints.

    Accepts Orchestrators or bare Agents. Agents are automatically
    wrapped in Solo for serving.

    Examples:
        ```python
        server = RunnableServer(agent)
        app = server.app  # FastAPI instance

        # Multi-runnable
        server = RunnableServer([agent1, pipeline, graph])

        # With custom factory (e.g. for testing)
        server = RunnableServer(factory=my_factory)
        ```
    """

    def __init__(
        self,
        runnables: Orchestrator | Agent | list[Orchestrator | Agent] | None = None,
        *,
        factory: RunnableFactory | None = None,
        title: str = "Tantra API",
        cors: bool = True,
    ):
        """Initialize the runnable server.

        Either ``runnables`` or ``factory`` must be provided. When
        ``runnables`` is provided, a ``PostgresRunnableFactory`` is created
        using ``DATABASE_URL`` from the environment during startup.

        Bare Agents are automatically wrapped in :class:`Solo`.

        When ``factory`` is provided, it is used directly (no pool or
        ``DATABASE_URL`` required). This is useful for testing.

        Args:
            runnables: A single Orchestrator/Agent or list to serve.
            factory: A RunnableFactory for session-isolated instances.
            title: Title for the OpenAPI docs. Default ``"Tantra API"``.
            cors: Whether to enable permissive CORS. Default ``True``.

        Raises:
            ValueError: If neither ``runnables`` nor ``factory`` is provided.
        """
        if factory is not None:
            self._factory: RunnableFactory | None = factory
            self._templates: dict[str, Orchestrator] | None = None
        elif runnables is not None:
            if not isinstance(runnables, list):
                runnables = [runnables]

            # Auto-wrap bare Agents in Solo
            wrapped: list[Orchestrator] = []
            for r in runnables:
                if isinstance(r, Agent):
                    wrapped.append(Solo(r))
                else:
                    wrapped.append(r)

            templates: dict[str, Orchestrator] = {}
            for i, r in enumerate(wrapped):
                name = r.name or f"runnable-{i}"
                if r.name is None and hasattr(r, "name"):
                    r.name = name
                templates[name] = r

            self._templates = templates
            self._factory = None
        else:
            raise ValueError("Either 'runnables' or 'factory' must be provided")

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            if self._factory is not None:
                yield
            else:
                dsn = os.environ.get("DATABASE_URL")
                if not dsn:
                    raise ConfigurationError("DATABASE_URL environment variable is required")
                pool = await asyncpg.create_pool(dsn=dsn)
                self._factory = PostgresRunnableFactory(self._templates, pool)
                yield
                await pool.close()

        self.app = FastAPI(title=title, lifespan=lifespan)

        if cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        self._setup_routes()

    @property
    def names(self) -> list[str]:
        """List of registered runnable names."""
        if self._factory is not None:
            return self._factory.names
        if self._templates is not None:
            return list(self._templates.keys())
        return []

    def _setup_routes(self) -> None:
        """Register all FastAPI routes."""

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            return HealthResponse(runnables=self.names)

        @self.app.get("/runnables", response_model=list[RunnableInfo])
        async def list_runnables():
            return self._factory.list_runnables()

        @self.app.post("/runnables/{name}/runs", response_model=RunResponse)
        async def create_run(name: str, request: RunRequest):
            if name not in self._factory.names:
                raise HTTPException(status_code=404, detail=f"Runnable '{name}' not found")

            session_id = request.session_id or str(uuid.uuid4())
            orchestrator = await self._factory.get(name, session_id)

            if request.stream:
                return await self._stream_run(orchestrator, request.message, session_id)

            try:
                result = await orchestrator.run(request.message, session_id=session_id)
                return RunResponse(
                    run_id=str(result.metadata.run_id),
                    session_id=session_id,
                    status="completed",
                    output=result.output,
                    metadata=result.metadata,
                    detail=_serialize_detail(result.detail),
                )
            except ExecutionInterruptedError as e:
                return await self._interrupt_response(e, session_id)
            except Exception as e:
                return RunResponse(
                    run_id="unknown",
                    session_id=session_id,
                    status="failed",
                    error=str(e),
                )

        @self.app.post("/runnables/{name}/resume", response_model=RunResponse)
        async def resume_run(name: str, request: ResumeRequest):
            if name not in self._factory.names:
                raise HTTPException(status_code=404, detail=f"Runnable '{name}' not found")

            store = self._factory.checkpoint_store
            if store is None:
                raise HTTPException(
                    status_code=501,
                    detail="Checkpoint store not available",
                )

            cp = await store.load(request.checkpoint_id)
            if cp is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Checkpoint not found: {request.checkpoint_id}",
                )

            session_id = cp.session_id or str(uuid.uuid4())
            orchestrator = await self._factory.get(name, session_id)

            response = None
            if request.response:
                response = InterruptResponse(
                    value=request.response.value,
                    proceed=request.response.proceed,
                    reason=request.response.reason,
                )

            try:
                result = await orchestrator.resume(request.checkpoint_id, response)
                return RunResponse(
                    run_id=str(result.metadata.run_id),
                    session_id=session_id,
                    status="completed",
                    output=result.output,
                    metadata=result.metadata,
                    detail=_serialize_detail(result.detail),
                )
            except ExecutionInterruptedError as e:
                return await self._interrupt_response(e, session_id)
            except Exception as e:
                return RunResponse(
                    run_id=str(cp.run_id),
                    session_id=session_id,
                    status="failed",
                    error=str(e),
                )

        @self.app.get(
            "/runnables/{name}/checkpoints",
            response_model=list[CheckpointSummary],
        )
        async def list_checkpoints(
            name: str,
            session_id: str | None = Query(default=None),
            status: str | None = Query(default=None),
        ):
            if name not in self._factory.names:
                raise HTTPException(status_code=404, detail=f"Runnable '{name}' not found")

            store = self._factory.checkpoint_store
            if store is None:
                return []

            checkpoints = await store.list_by_name(
                name=name, session_id=session_id, status=status
            )
            return [
                CheckpointSummary(
                    id=cp.id,
                    run_id=str(cp.run_id),
                    session_id=cp.session_id,
                    checkpoint_type=cp.checkpoint_type,
                    name=cp.name,
                    status=cp.status,
                    created_at=cp.created_at.isoformat(),
                )
                for cp in checkpoints
            ]

        @self.app.get(
            "/runnables/{name}/checkpoints/{checkpoint_id}",
            response_model=CheckpointSummary,
        )
        async def get_checkpoint(name: str, checkpoint_id: str):
            if name not in self._factory.names:
                raise HTTPException(status_code=404, detail=f"Runnable '{name}' not found")

            store = self._factory.checkpoint_store
            if store is None:
                raise HTTPException(status_code=404, detail="Checkpoint not found")

            cp = await store.load(checkpoint_id)
            if cp is None:
                raise HTTPException(status_code=404, detail="Checkpoint not found")

            return CheckpointSummary(
                id=cp.id,
                run_id=str(cp.run_id),
                session_id=cp.session_id,
                checkpoint_type=cp.checkpoint_type,
                name=cp.name,
                status=cp.status,
                created_at=cp.created_at.isoformat(),
            )

    async def _interrupt_response(
        self, error: ExecutionInterruptedError, session_id: str
    ) -> RunResponse:
        """Build a RunResponse for an interrupted execution.

        Args:
            error: The interrupt error.
            session_id: The session ID for the response.

        Returns:
            RunResponse with status "interrupted".
        """
        run_id = "unknown"
        store = self._factory.checkpoint_store
        if store is not None:
            cp = await store.load(error.checkpoint_id)
            if cp is not None:
                run_id = str(cp.run_id)
        return RunResponse(
            run_id=run_id,
            session_id=session_id,
            status="interrupted",
            checkpoint_id=error.checkpoint_id,
            prompt=error.prompt,
        )

    async def _stream_run(
        self, orchestrator: Orchestrator, message: str, session_id: str
    ) -> StreamingResponse:
        """Create an SSE streaming response.

        Uses ``orchestrator.stream()`` which yields ``StreamEvent`` objects.
        Each event is serialised as an SSE ``data:`` line. The unified stream
        contains tokens, tool events, orchestration events, and the final
        ``complete`` event — all interleaved.

        Args:
            orchestrator: The orchestrator to stream.
            message: The user message.
            session_id: The session ID.

        Returns:
            A StreamingResponse yielding SSE events.
        """

        async def event_generator():
            try:
                async for event in orchestrator.stream(message, session_id=session_id):
                    if event.type == "complete":
                        metadata = event.data.get("metadata")
                        done = {
                            "event": "complete",
                            "done": True,
                            "status": "completed",
                            "session_id": session_id,
                            "output": event.data.get("output", ""),
                        }
                        if metadata is not None:
                            done["run_id"] = str(metadata.run_id)
                            done["metadata"] = metadata.model_dump(mode="json")
                        done["detail"] = _serialize_detail(event.data.get("detail"))
                        yield f"data: {json.dumps(done)}\n\n"
                    else:
                        yield f"data: {json.dumps({'event': event.type, **event.data})}\n\n"
            except ExecutionInterruptedError as e:
                done = {
                    "event": "interrupted",
                    "done": True,
                    "status": "interrupted",
                    "checkpoint_id": e.checkpoint_id,
                    "prompt": e.prompt,
                    "session_id": session_id,
                }
                yield f"data: {json.dumps(done)}\n\n"
            except Exception as e:
                done = {
                    "event": "error",
                    "done": True,
                    "status": "failed",
                    "error": str(e),
                    "session_id": session_id,
                }
                yield f"data: {json.dumps(done)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )


def serve(
    runnables: Orchestrator | Agent | list[Orchestrator | Agent],
    *,
    title: str = "Tantra API",
    cors: bool = True,
    run: bool = False,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> FastAPI:
    """Create (and optionally run) an HTTP server for Tantra orchestrators.

    This is the main entry point for serving. Returns a FastAPI
    application that can be used with any ASGI server.

    Bare Agents are automatically wrapped in :class:`Solo`.

    Args:
        runnables: A single Orchestrator/Agent or list to serve.
        title: Title for the OpenAPI docs.
        cors: Whether to enable permissive CORS. Default True.
        run: If True, starts uvicorn immediately (blocking). Default False.
        host: Host to bind to when run=True. Default "0.0.0.0".
        port: Port to bind to when run=True. Default 8000.

    Returns:
        The FastAPI application instance.

    Examples:
        ```python
        # Return app for external ASGI server
        app = serve(agent)

        # Run directly
        serve(agent, run=True, port=8000)

        # Multiple runnables
        app = serve([agent1, pipeline, graph])
        ```
    """
    server = RunnableServer(runnables, title=title, cors=cors)

    if run:
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "uvicorn is required to run the server. Install with: pip install tantra[serve]"
            )
        uvicorn.run(server.app, host=host, port=port)

    return server.app
