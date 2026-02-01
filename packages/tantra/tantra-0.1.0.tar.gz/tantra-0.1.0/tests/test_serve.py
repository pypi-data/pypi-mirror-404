"""Tests for the serve module."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from conftest import MemoryCheckpointStore, MockProvider

from tantra import Agent, ToolSet, tool
from tantra.checkpoints import Checkpoint, CheckpointStore
from tantra.engine import ExecutionInterruptedError
from tantra.orchestration.solo import Solo
from tantra.types import RunMetadata

try:
    from fastapi.testclient import TestClient

    from tantra.serve import RunnableServer, serve
    from tantra.serve.factory import RunnableFactory
    from tantra.serve.models import RunnableInfo

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

pytestmark = pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed")


class TestableFactory(RunnableFactory):
    """In-memory factory for tests — no Postgres required."""

    def __init__(
        self,
        templates: dict[str, Agent],
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        self._templates = templates
        self._sessions: dict[str, dict[str, Agent]] = {}
        self._checkpoint_store_instance = checkpoint_store

    @property
    def names(self) -> list[str]:
        return list(self._templates.keys())

    @property
    def checkpoint_store(self) -> CheckpointStore | None:
        return self._checkpoint_store_instance

    async def get(self, name: str, session_id: str) -> Solo:
        if name not in self._templates:
            raise KeyError(f"'{name}' not found")
        if name not in self._sessions:
            self._sessions[name] = {}
        if session_id not in self._sessions[name]:
            self._sessions[name][session_id] = Solo(self._templates[name].clone())
        return self._sessions[name][session_id]

    def list_runnables(self) -> list[RunnableInfo]:
        result = []
        for name, runnable in self._templates.items():
            tool_names = []
            if runnable.tools:
                tool_names = runnable.tools.names
            result.append(
                RunnableInfo(
                    name=name,
                    has_system_prompt=bool(runnable.system_prompt),
                    tools=tool_names,
                )
            )
        return result


@pytest.fixture
def simple_agent():
    provider = MockProvider(responses=["Hello from the agent!"])
    return Agent(provider, system_prompt="You are helpful.", name="test-agent")


@pytest.fixture
def tool_agent():
    @tool
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}!"

    provider = MockProvider(responses=["I greeted them."])
    return Agent(
        provider,
        tools=ToolSet([greet]),
        system_prompt="You can greet people.",
        name="greeter",
    )


@pytest.fixture
def factory(simple_agent):
    return TestableFactory({"test-agent": simple_agent})


@pytest.fixture
def multi_factory(simple_agent, tool_agent):
    return TestableFactory({"test-agent": simple_agent, "greeter": tool_agent})


@pytest.fixture
def client(factory):
    server = RunnableServer(factory=factory)
    return TestClient(server.app)


@pytest.fixture
def multi_client(multi_factory):
    server = RunnableServer(factory=multi_factory)
    return TestClient(server.app)


class TestRunnableServerCreation:
    def test_with_factory(self, factory):
        server = RunnableServer(factory=factory)
        assert server.names == ["test-agent"]

    def test_with_factory_multiple(self, multi_factory):
        server = RunnableServer(factory=multi_factory)
        assert set(server.names) == {"test-agent", "greeter"}

    def test_custom_title(self, factory):
        server = RunnableServer(factory=factory, title="My API")
        assert server.app.title == "My API"

    def test_no_args_raises(self):
        with pytest.raises(ValueError, match="Either"):
            RunnableServer()


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["runnables"] == ["test-agent"]

    def test_health_multi(self, multi_client):
        resp = multi_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["runnables"]) == {"test-agent", "greeter"}


class TestRunnablesEndpoint:
    def test_list(self, client):
        resp = client.get("/runnables")
        assert resp.status_code == 200
        runnables = resp.json()
        assert len(runnables) == 1
        assert runnables[0]["name"] == "test-agent"
        assert runnables[0]["has_system_prompt"] is True
        assert runnables[0]["tools"] == []

    def test_list_with_tools(self, multi_client):
        resp = multi_client.get("/runnables")
        runnables = resp.json()
        greeter = next(r for r in runnables if r["name"] == "greeter")
        assert "greet" in greeter["tools"]


class TestRun:
    def test_run(self, client):
        resp = client.post(
            "/runnables/test-agent/runs",
            json={"message": "Hi"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["output"] == "Hello from the agent!"
        assert "run_id" in data
        assert "session_id" in data
        assert "metadata" in data

    def test_run_auto_generates_session_id(self, client):
        resp = client.post(
            "/runnables/test-agent/runs",
            json={"message": "Hi"},
        )
        data = resp.json()
        assert data["session_id"]  # not None or empty
        # Should be a UUID
        from uuid import UUID

        UUID(data["session_id"])

    def test_run_echoes_session_id(self, client):
        resp = client.post(
            "/runnables/test-agent/runs",
            json={"message": "Hi", "session_id": "my-session"},
        )
        data = resp.json()
        assert data["session_id"] == "my-session"

    def test_run_unknown_runnable(self, client):
        resp = client.post(
            "/runnables/nope/runs",
            json={"message": "Hi"},
        )
        assert resp.status_code == 404

    def test_run_failed(self):
        """Agent that raises returns status=failed."""
        provider = MockProvider(responses=["ok"])
        agent = Agent(provider, name="fail-agent")
        factory = TestableFactory({"fail-agent": agent})
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        with patch.object(Agent, "run", side_effect=RuntimeError("boom")):
            resp = client.post(
                "/runnables/fail-agent/runs",
                json={"message": "Hi"},
            )
        data = resp.json()
        assert data["status"] == "failed"
        assert "boom" in data["error"]


class TestRunWithSession:
    def test_session_continuity(self):
        provider = MockProvider(responses=["First reply", "Second reply", "Third reply"])
        agent = Agent(provider, name="test")
        factory = TestableFactory({"test": agent})
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        r1 = client.post(
            "/runnables/test/runs",
            json={"message": "msg1", "session_id": "s1"},
        )
        r2 = client.post(
            "/runnables/test/runs",
            json={"message": "msg2", "session_id": "s1"},
        )

        assert r1.json()["output"] == "First reply"
        assert r2.json()["output"] == "Second reply"
        assert r1.json()["session_id"] == "s1"
        assert r2.json()["session_id"] == "s1"

    def test_different_sessions_isolated(self):
        provider = MockProvider(responses=["Reply A", "Reply B"])
        agent = Agent(provider, name="test")
        factory = TestableFactory({"test": agent})
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        r1 = client.post(
            "/runnables/test/runs",
            json={"message": "Hi", "session_id": "a"},
        )
        r2 = client.post(
            "/runnables/test/runs",
            json={"message": "Hi", "session_id": "b"},
        )

        assert r1.json()["session_id"] == "a"
        assert r2.json()["session_id"] == "b"


class TestRunStreaming:
    def test_stream(self, client):
        with client.stream(
            "POST",
            "/runnables/test-agent/runs",
            json={"message": "Hi", "stream": True},
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"

            events = []
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

        assert len(events) >= 1
        assert events[-1]["done"] is True
        assert events[-1]["status"] == "completed"
        assert "output" in events[-1]
        assert "session_id" in events[-1]


class TestRunInterrupt:
    def test_interrupt_returns_structured_response(self):
        provider = MockProvider(responses=["ok"])
        agent = Agent(provider, name="int-agent")
        store = MemoryCheckpointStore()
        factory = TestableFactory({"int-agent": agent}, checkpoint_store=store)
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        run_id = uuid4()
        cp = Checkpoint(
            id="cp-123",
            run_id=run_id,
            name="int-agent",
            messages=[],
            status="pending",
        )

        async def save_and_raise(*args, **kwargs):
            await store.save(cp)
            raise ExecutionInterruptedError("cp-123", "Approve this?")

        with patch.object(Agent, "run", side_effect=save_and_raise):
            resp = client.post(
                "/runnables/int-agent/runs",
                json={"message": "Do something"},
            )

        data = resp.json()
        assert data["status"] == "interrupted"
        assert data["checkpoint_id"] == "cp-123"
        assert data["prompt"] == "Approve this?"
        assert data["run_id"] == str(run_id)
        assert "session_id" in data


class TestResume:
    def test_resume(self):
        provider = MockProvider(responses=["Resumed output"])
        agent = Agent(provider, name="res-agent")
        store = MemoryCheckpointStore()
        factory = TestableFactory({"res-agent": agent}, checkpoint_store=store)
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        run_id = uuid4()
        cp = Checkpoint(
            id="cp-456",
            run_id=run_id,
            session_id="sess-1",
            name="res-agent",
            messages=[],
            status="pending",
        )
        # Save checkpoint directly into the in-memory store
        store._checkpoints[cp.id] = cp

        mock_result = AsyncMock()
        mock_result.output = "Resumed output"
        mock_result.metadata = RunMetadata(run_id=run_id)
        mock_result.detail = None

        with patch.object(Agent, "resume", return_value=mock_result):
            resp = client.post(
                "/runnables/res-agent/resume",
                json={"checkpoint_id": "cp-456"},
            )

        data = resp.json()
        assert data["status"] == "completed"
        assert data["output"] == "Resumed output"
        assert data["session_id"] == "sess-1"

    def test_resume_not_found(self):
        provider = MockProvider(responses=["ok"])
        agent = Agent(provider, name="res-agent")
        store = MemoryCheckpointStore()
        factory = TestableFactory({"res-agent": agent}, checkpoint_store=store)
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        resp = client.post(
            "/runnables/res-agent/resume",
            json={"checkpoint_id": "nonexistent"},
        )
        assert resp.status_code == 404

    def test_resume_unknown_runnable(self):
        provider = MockProvider(responses=["ok"])
        agent = Agent(provider, name="res-agent")
        store = MemoryCheckpointStore()
        factory = TestableFactory({"res-agent": agent}, checkpoint_store=store)
        server = RunnableServer(factory=factory)
        client = TestClient(server.app)

        resp = client.post(
            "/runnables/nope/resume",
            json={"checkpoint_id": "cp-456"},
        )
        assert resp.status_code == 404


class TestCheckpoints:
    def _make_server(self):
        provider = MockProvider(responses=["ok"])
        agent = Agent(provider, name="cp-agent")
        store = MemoryCheckpointStore()
        factory = TestableFactory({"cp-agent": agent}, checkpoint_store=store)
        server = RunnableServer(factory=factory)
        return TestClient(server.app), store

    def test_list_empty(self):
        client, _ = self._make_server()
        resp = client.get("/runnables/cp-agent/checkpoints")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_checkpoints(self):
        client, store = self._make_server()

        cp = Checkpoint(
            id="cp-1",
            run_id=uuid4(),
            session_id="s1",
            checkpoint_type="graph_progress",
            name="cp-agent",
            messages=[],
            status="pending",
        )
        store._checkpoints[cp.id] = cp

        resp = client.get("/runnables/cp-agent/checkpoints")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "cp-1"
        assert data[0]["checkpoint_type"] == "graph_progress"
        assert data[0]["status"] == "pending"

    def test_list_filtered_by_status(self):
        client, store = self._make_server()

        for i, status in enumerate(["pending", "completed", "pending"]):
            cp = Checkpoint(
                id=f"cp-{i}",
                run_id=uuid4(),
                name="cp-agent",
                messages=[],
                status=status,
            )
            store._checkpoints[cp.id] = cp

        resp = client.get("/runnables/cp-agent/checkpoints?status=pending")
        data = resp.json()
        assert len(data) == 2

    def test_list_filtered_by_session_id(self):
        client, store = self._make_server()

        for i, sid in enumerate(["s1", "s2", "s1"]):
            cp = Checkpoint(
                id=f"cp-{i}",
                run_id=uuid4(),
                session_id=sid,
                name="cp-agent",
                messages=[],
                status="pending",
            )
            store._checkpoints[cp.id] = cp

        resp = client.get("/runnables/cp-agent/checkpoints?session_id=s1")
        data = resp.json()
        assert len(data) == 2

    def test_get_checkpoint(self):
        client, store = self._make_server()

        run_id = uuid4()
        cp = Checkpoint(
            id="cp-detail",
            run_id=run_id,
            session_id="s1",
            checkpoint_type="swarm_progress",
            name="cp-agent",
            messages=[],
            status="pending",
        )
        store._checkpoints[cp.id] = cp

        resp = client.get("/runnables/cp-agent/checkpoints/cp-detail")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "cp-detail"
        assert data["run_id"] == str(run_id)
        assert data["checkpoint_type"] == "swarm_progress"

    def test_get_checkpoint_not_found(self):
        client, _ = self._make_server()
        resp = client.get("/runnables/cp-agent/checkpoints/nonexistent")
        assert resp.status_code == 404

    def test_list_unknown_runnable(self):
        client, _ = self._make_server()
        resp = client.get("/runnables/nope/checkpoints")
        assert resp.status_code == 404


class TestServeFunction:
    def test_serve_returns_fastapi_app(self, simple_agent):
        app = serve(simple_agent)
        assert app is not None
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_serve_custom_title(self, simple_agent):
        app = serve(simple_agent, title="Custom Title")
        assert app.title == "Custom Title"

    def test_serve_no_cors(self, simple_agent):
        app = serve(simple_agent, cors=False)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
