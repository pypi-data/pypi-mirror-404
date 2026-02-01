"""Tests for Evaluation-Gated Deployment."""

from uuid import uuid4

import pytest
from conftest import MockProvider

from tantra import (
    Agent,
    DegradationThresholds,
    DeploymentGate,
    DeploymentResult,
    DeploymentStatus,
    FileBaselineStore,
    PerformanceBaseline,
    PerformanceMonitor,
    deploy_with_gate,
)
from tantra.evaluation import EvalCase, EvalSuite, contains
from tantra.types import RunMetadata


class TestPerformanceBaseline:
    """Tests for PerformanceBaseline."""

    def test_create_baseline(self):
        """Create a performance baseline."""
        baseline = PerformanceBaseline(
            pass_rate=0.95,
            avg_cost=0.002,
            avg_tokens=100,
            avg_latency_ms=150,
            sample_size=50,
        )

        assert baseline.pass_rate == 0.95
        assert baseline.avg_cost == 0.002
        assert baseline.avg_tokens == 100
        assert baseline.avg_latency_ms == 150

    def test_baseline_serialization(self):
        """Baseline converts to/from dict."""
        baseline = PerformanceBaseline(
            pass_rate=0.90,
            avg_cost=0.001,
            avg_tokens=50,
            avg_latency_ms=100,
        )

        data = baseline.to_dict()
        restored = PerformanceBaseline.from_dict(data)

        assert restored.pass_rate == baseline.pass_rate
        assert restored.avg_cost == baseline.avg_cost
        assert restored.avg_tokens == baseline.avg_tokens


class TestDeploymentGate:
    """Tests for DeploymentGate."""

    @pytest.fixture
    def simple_suite(self):
        """Create simple evaluation suite."""
        suite = EvalSuite()
        suite.add_test(EvalCase(input="Hi", matchers=[contains("Hello")]))
        suite.add_test(EvalCase(input="Bye", matchers=[contains("Goodbye")]))
        return suite

    @pytest.fixture
    def passing_agent(self):
        """Create agent that passes all tests."""
        provider = MockProvider(responses=["Hello!", "Goodbye!"])
        return Agent(provider)

    @pytest.fixture
    def failing_agent(self):
        """Create agent that fails tests."""
        provider = MockProvider(responses=["Wrong", "Also wrong"])
        return Agent(provider)

    @pytest.mark.asyncio
    async def test_gate_passes_good_agent(self, simple_suite, passing_agent):
        """Gate passes agent that meets requirements."""
        gate = DeploymentGate(suite=simple_suite, min_pass_rate=0.90)

        result = await gate.evaluate(passing_agent, version="1.0.0")

        assert result.status == DeploymentStatus.PASSED
        assert result.can_deploy is True

    @pytest.mark.asyncio
    async def test_gate_fails_bad_agent(self, simple_suite, failing_agent):
        """Gate fails agent below pass rate."""
        gate = DeploymentGate(suite=simple_suite, min_pass_rate=0.90)

        result = await gate.evaluate(failing_agent, version="1.0.0")

        assert result.status == DeploymentStatus.FAILED
        assert result.can_deploy is False
        assert "Pass rate" in result.message

    @pytest.mark.asyncio
    async def test_gate_cost_threshold(self, simple_suite, passing_agent):
        """Gate enforces cost threshold."""
        gate = DeploymentGate(
            suite=simple_suite,
            min_pass_rate=0.50,
            max_cost_per_run=0.0000001,  # Impossibly low threshold
        )

        result = await gate.evaluate(passing_agent, version="1.0.0")

        # Should fail on cost even if pass rate is OK
        assert result.status == DeploymentStatus.FAILED
        assert "cost" in result.message.lower()

    @pytest.mark.asyncio
    async def test_gate_saves_baseline(self, simple_suite, passing_agent):
        """Gate saves baseline on success."""
        gate = DeploymentGate(suite=simple_suite, min_pass_rate=0.50)

        assert gate.baseline is None

        result = await gate.evaluate(passing_agent, version="1.0.0", save_baseline=True)

        assert result.status == DeploymentStatus.PASSED
        assert gate.baseline is not None
        assert gate.baseline.pass_rate > 0

    @pytest.mark.asyncio
    async def test_gate_detects_degradation(self, simple_suite, failing_agent):
        """Gate detects degradation from baseline."""
        # Set a high baseline
        baseline = PerformanceBaseline(
            pass_rate=1.0,
            avg_cost=0.001,
            avg_tokens=50,
            avg_latency_ms=100,
        )

        gate = DeploymentGate(
            suite=simple_suite,
            min_pass_rate=0.0,  # Low threshold so it doesn't fail on pass rate
            baseline=baseline,
            thresholds=DegradationThresholds(max_pass_rate_drop=0.1),
        )

        result = await gate.evaluate(failing_agent, version="2.0.0")

        assert result.status == DeploymentStatus.DEGRADED
        assert "degraded" in result.message.lower()

    def test_record_deployment(self, simple_suite):
        """Recording deployment updates history."""
        gate = DeploymentGate(suite=simple_suite, min_pass_rate=0.50)

        result = DeploymentResult(
            status=DeploymentStatus.PASSED,
            version="1.0.0",
        )

        gate.record_deployment(result)

        history = gate.get_deployment_history()
        assert len(history) == 1
        assert history[0].version == "1.0.0"
        assert history[0].status == DeploymentStatus.DEPLOYED


class TestDegradationThresholds:
    """Tests for DegradationThresholds."""

    def test_default_thresholds(self):
        """Default thresholds are reasonable."""
        thresholds = DegradationThresholds()

        assert thresholds.max_pass_rate_drop == 0.1
        assert thresholds.max_cost_increase == 0.5
        assert thresholds.max_latency_increase == 1.0

    def test_custom_thresholds(self):
        """Can set custom thresholds."""
        thresholds = DegradationThresholds(
            max_pass_rate_drop=0.05,
            max_cost_increase=0.25,
            max_latency_increase=0.5,
        )

        assert thresholds.max_pass_rate_drop == 0.05
        assert thresholds.max_cost_increase == 0.25


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor."""

    @pytest.fixture
    def baseline(self):
        """Create test baseline."""
        return PerformanceBaseline(
            pass_rate=1.0,
            avg_cost=0.001,
            avg_tokens=50,
            avg_latency_ms=100,
        )

    def test_record_runs(self, baseline):
        """Monitor tracks run metrics."""
        monitor = PerformanceMonitor(baseline=baseline)

        metadata = RunMetadata(
            run_id=uuid4(),
            total_tokens=50,
            prompt_tokens=30,
            completion_tokens=20,
            estimated_cost=0.001,
            duration_ms=100,
            tool_calls_count=0,
        )

        monitor.record_run(metadata)

        metrics = monitor.get_current_metrics()
        assert metrics is not None
        assert metrics["sample_size"] == 1

    def test_detects_latency_degradation(self, baseline):
        """Monitor detects latency increase."""
        alerts = []

        monitor = PerformanceMonitor(
            baseline=baseline,
            thresholds=DegradationThresholds(
                max_latency_increase=0.5,
                min_sample_size=3,
            ),
            on_degradation=lambda m: alerts.append(m),
        )

        # Add runs with high latency (3x baseline)
        for _ in range(5):
            monitor.record_run(
                RunMetadata(
                    run_id=uuid4(),
                    total_tokens=50,
                    prompt_tokens=30,
                    completion_tokens=20,
                    estimated_cost=0.001,
                    duration_ms=300,  # 3x the baseline!
                    tool_calls_count=0,
                )
            )

        assert monitor.is_degraded()
        assert len(alerts) == 1
        assert "latency" in alerts[0].lower()

    def test_detects_cost_degradation(self, baseline):
        """Monitor detects cost increase."""
        monitor = PerformanceMonitor(
            baseline=baseline,
            thresholds=DegradationThresholds(
                max_cost_increase=0.5,
                min_sample_size=3,
            ),
        )

        # Add runs with high cost
        for _ in range(5):
            monitor.record_run(
                RunMetadata(
                    run_id=uuid4(),
                    total_tokens=100,
                    prompt_tokens=60,
                    completion_tokens=40,
                    estimated_cost=0.005,  # 5x the baseline!
                    duration_ms=100,
                    tool_calls_count=0,
                )
            )

        assert monitor.is_degraded()
        assert "cost" in monitor.get_degradation_message().lower()

    def test_no_degradation_within_threshold(self, baseline):
        """Monitor doesn't alert for small variations."""
        monitor = PerformanceMonitor(
            baseline=baseline,
            thresholds=DegradationThresholds(
                max_latency_increase=0.5,
                min_sample_size=3,
            ),
        )

        # Add runs with slightly higher latency (within threshold)
        for _ in range(5):
            monitor.record_run(
                RunMetadata(
                    run_id=uuid4(),
                    total_tokens=50,
                    prompt_tokens=30,
                    completion_tokens=20,
                    estimated_cost=0.001,
                    duration_ms=130,  # 30% increase, under 50% threshold
                    tool_calls_count=0,
                )
            )

        assert not monitor.is_degraded()

    def test_window_size(self, baseline):
        """Monitor respects window size."""
        monitor = PerformanceMonitor(
            baseline=baseline,
            window_size=5,
        )

        # Add more runs than window size
        for _ in range(10):
            monitor.record_run(
                RunMetadata(
                    run_id=uuid4(),
                    total_tokens=50,
                    prompt_tokens=30,
                    completion_tokens=20,
                    estimated_cost=0.001,
                    duration_ms=100,
                    tool_calls_count=0,
                )
            )

        metrics = monitor.get_current_metrics()
        assert metrics["sample_size"] == 5  # Only keeps last 5

    def test_reset(self, baseline):
        """Reset clears monitor state."""
        monitor = PerformanceMonitor(baseline=baseline)

        monitor.record_run(
            RunMetadata(
                run_id=uuid4(),
                total_tokens=50,
                prompt_tokens=30,
                completion_tokens=20,
                estimated_cost=0.001,
                duration_ms=100,
                tool_calls_count=0,
            )
        )

        monitor.reset()

        assert monitor.get_current_metrics() is None
        assert not monitor.is_degraded()


class TestFileBaselineStore:
    """Tests for FileBaselineStore."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create store in temp directory."""
        return FileBaselineStore(str(tmp_path / "baselines"))

    @pytest.mark.asyncio
    async def test_save_and_load(self, store):
        """Save and load baseline."""
        baseline = PerformanceBaseline(
            pass_rate=0.95,
            avg_cost=0.002,
            avg_tokens=75,
            avg_latency_ms=200,
        )

        await store.save("my-agent", baseline)
        loaded = await store.load("my-agent")

        assert loaded is not None
        assert loaded.pass_rate == 0.95
        assert loaded.avg_cost == 0.002

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, store):
        """Load returns None for nonexistent agent."""
        loaded = await store.load("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_agents(self, store):
        """List all agents with baselines."""
        baseline = PerformanceBaseline(
            pass_rate=0.90,
            avg_cost=0.001,
            avg_tokens=50,
            avg_latency_ms=100,
        )

        await store.save("agent-1", baseline)
        await store.save("agent-2", baseline)
        await store.save("agent-3", baseline)

        agents = await store.list_agents()
        assert len(agents) == 3
        assert "agent-1" in agents
        assert "agent-2" in agents


class TestDeployWithGate:
    """Tests for deploy_with_gate helper."""

    @pytest.mark.asyncio
    async def test_deploys_on_pass(self):
        """Calls deploy_fn on successful evaluation."""
        suite = EvalSuite()
        suite.add_test(EvalCase(input="Hi", matchers=[contains("Hello")]))

        provider = MockProvider(responses=["Hello!"])
        agent = Agent(provider)

        gate = DeploymentGate(suite=suite, min_pass_rate=0.50)

        deployed = []
        result = await deploy_with_gate(
            agent=agent,
            gate=gate,
            version="1.0.0",
            deploy_fn=lambda a: deployed.append(a),
        )

        assert result.status == DeploymentStatus.DEPLOYED
        assert len(deployed) == 1

    @pytest.mark.asyncio
    async def test_no_deploy_on_fail(self):
        """Does not call deploy_fn on failed evaluation."""
        suite = EvalSuite()
        suite.add_test(EvalCase(input="Hi", matchers=[contains("Hello")]))

        provider = MockProvider(responses=["Wrong"])
        agent = Agent(provider)

        gate = DeploymentGate(suite=suite, min_pass_rate=0.90)

        deployed = []
        result = await deploy_with_gate(
            agent=agent,
            gate=gate,
            version="1.0.0",
            deploy_fn=lambda a: deployed.append(a),
        )

        assert result.status == DeploymentStatus.FAILED
        assert len(deployed) == 0
