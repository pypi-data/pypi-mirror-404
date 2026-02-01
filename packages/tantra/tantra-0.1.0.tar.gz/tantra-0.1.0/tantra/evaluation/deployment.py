"""Evaluation-Gated Deployment for Tantra.

Provides mechanisms to ensure agents pass evaluation tests before deployment,
monitor performance in production, and trigger rollback on degradation.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from ..types import RunMetadata
from .base import BaselineStore, PerformanceBaseline
from .suite import EvalResult, EvalSuite

if TYPE_CHECKING:
    from ..agent import Agent


class DeploymentStatus(str, Enum):
    """Status of a deployment."""

    PENDING = "pending"
    EVALUATING = "evaluating"
    PASSED = "passed"
    FAILED = "failed"
    DEPLOYED = "deployed"
    DEGRADED = "degraded"
    ROLLED_BACK = "rolled_back"


@dataclass
class DegradationThresholds:
    """Thresholds for detecting performance degradation.

    Attributes:
        max_pass_rate_drop: Maximum allowed drop in pass rate before degradation.
        max_cost_increase: Maximum allowed fractional cost increase.
        max_latency_increase: Maximum allowed fractional latency increase.
        min_sample_size: Minimum number of samples before comparing to baseline.
    """

    max_pass_rate_drop: float = 0.1  # 10% drop triggers degradation
    max_cost_increase: float = 0.5  # 50% cost increase
    max_latency_increase: float = 1.0  # 100% latency increase
    min_sample_size: int = 10  # Minimum samples before comparing


@dataclass
class DeploymentResult:
    """Result of a deployment attempt.

    Attributes:
        status: Current deployment status.
        version: Version string for this deployment.
        evaluation_result: Evaluation results, if evaluation was run.
        baseline: Performance baseline used or created.
        message: Human-readable status message.
        deployed_at: Timestamp when deployment occurred.
        rolled_back_at: Timestamp when rollback occurred, if applicable.
    """

    status: DeploymentStatus
    version: str
    evaluation_result: EvalResult | None = None
    baseline: PerformanceBaseline | None = None
    message: str = ""
    deployed_at: datetime | None = None
    rolled_back_at: datetime | None = None

    @property
    def can_deploy(self) -> bool:
        """Whether this result allows deployment."""
        return self.status == DeploymentStatus.PASSED


class DeploymentGate:
    """Gate that controls agent deployment based on evaluation results.

    Ensures agents pass evaluation tests before deployment.
    Can also check against baseline performance for existing agents.

    Examples:
        ```python
        # Create evaluation suite
        suite = EvalSuite()
        suite.add_test(EvalCase(input="Hello", matchers=[contains("hello")]))
        suite.add_test(EvalCase(input="2+2?", matchers=[contains("4")]))

        # Create deployment gate
        gate = DeploymentGate(
            suite=suite,
            min_pass_rate=0.95,
            max_cost_per_run=0.10,
        )

        # Check if agent can be deployed
        result = await gate.evaluate(agent, version="1.0.0")
        if result.can_deploy:
            # Deploy the agent
            await deploy_agent(agent)
            gate.record_deployment(result)
        ```
    """

    def __init__(
        self,
        suite: EvalSuite,
        min_pass_rate: float = 0.95,
        max_cost_per_run: float | None = None,
        max_latency_ms: float | None = None,
        baseline: PerformanceBaseline | None = None,
        thresholds: DegradationThresholds | None = None,
    ):
        """Initialize deployment gate.

        Args:
            suite: Evaluation suite to run.
            min_pass_rate: Minimum pass rate required (0.0 to 1.0).
            max_cost_per_run: Maximum average cost per run.
            max_latency_ms: Maximum average latency in milliseconds.
            baseline: Optional baseline to compare against.
            thresholds: Thresholds for degradation detection.
        """
        self.suite = suite
        self.min_pass_rate = min_pass_rate
        self.max_cost_per_run = max_cost_per_run
        self.max_latency_ms = max_latency_ms
        self.baseline = baseline
        self.thresholds = thresholds or DegradationThresholds()

        self._deployments: list[DeploymentResult] = []

    async def evaluate(
        self,
        agent: Agent,
        version: str,
        save_baseline: bool = True,
    ) -> DeploymentResult:
        """Evaluate an agent for deployment.

        Args:
            agent: The agent to evaluate.
            version: Version string for this deployment.
            save_baseline: Whether to save result as new baseline if passed.

        Returns:
            DeploymentResult indicating pass/fail and metrics.
        """
        # Run evaluation
        eval_result = await self.suite.run(agent)

        # Check pass rate
        if eval_result.metrics.pass_rate < self.min_pass_rate:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                version=version,
                evaluation_result=eval_result,
                message=f"Pass rate {eval_result.metrics.pass_rate:.1%} below minimum {self.min_pass_rate:.1%}",
            )

        # Check cost threshold
        if self.max_cost_per_run and eval_result.metrics.average_cost > self.max_cost_per_run:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                version=version,
                evaluation_result=eval_result,
                message=f"Average cost ${eval_result.metrics.average_cost:.4f} exceeds maximum ${self.max_cost_per_run:.4f}",
            )

        # Check latency threshold
        if self.max_latency_ms and eval_result.metrics.average_duration_ms > self.max_latency_ms:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                version=version,
                evaluation_result=eval_result,
                message=f"Average latency {eval_result.metrics.average_duration_ms:.0f}ms exceeds maximum {self.max_latency_ms:.0f}ms",
            )

        # Check against baseline if exists
        if self.baseline:
            degradation = self._check_degradation(eval_result)
            if degradation:
                return DeploymentResult(
                    status=DeploymentStatus.DEGRADED,
                    version=version,
                    evaluation_result=eval_result,
                    baseline=self.baseline,
                    message=degradation,
                )

        # All checks passed
        new_baseline = PerformanceBaseline.from_evaluation(eval_result)

        if save_baseline:
            self.baseline = new_baseline

        return DeploymentResult(
            status=DeploymentStatus.PASSED,
            version=version,
            evaluation_result=eval_result,
            baseline=new_baseline,
            message="All evaluation checks passed",
        )

    def _check_degradation(self, result: EvalResult) -> str | None:
        """Check if results show degradation from baseline.

        Returns:
            Error message if degraded, None if OK.
        """
        if not self.baseline:
            return None

        metrics = result.metrics
        baseline = self.baseline
        thresholds = self.thresholds

        # Check pass rate drop
        pass_rate_drop = baseline.pass_rate - metrics.pass_rate
        if pass_rate_drop > thresholds.max_pass_rate_drop:
            return (
                f"Pass rate degraded by {pass_rate_drop:.1%} "
                f"(baseline: {baseline.pass_rate:.1%}, current: {metrics.pass_rate:.1%})"
            )

        # Check cost increase
        if baseline.avg_cost > 0:
            cost_increase = (metrics.average_cost - baseline.avg_cost) / baseline.avg_cost
            if cost_increase > thresholds.max_cost_increase:
                return (
                    f"Cost increased by {cost_increase:.1%} "
                    f"(baseline: ${baseline.avg_cost:.4f}, current: ${metrics.average_cost:.4f})"
                )

        # Check latency increase
        if baseline.avg_latency_ms > 0:
            latency_increase = (
                metrics.average_duration_ms - baseline.avg_latency_ms
            ) / baseline.avg_latency_ms
            if latency_increase > thresholds.max_latency_increase:
                return (
                    f"Latency increased by {latency_increase:.1%} "
                    f"(baseline: {baseline.avg_latency_ms:.0f}ms, current: {metrics.average_duration_ms:.0f}ms)"
                )

        return None

    def record_deployment(self, result: DeploymentResult) -> None:
        """Record a deployment result.

        Args:
            result: The deployment result to record.
        """
        result.deployed_at = datetime.now(UTC)
        result.status = DeploymentStatus.DEPLOYED
        self._deployments.append(result)

    def get_deployment_history(self) -> list[DeploymentResult]:
        """Get deployment history."""
        return self._deployments.copy()

    def get_current_baseline(self) -> PerformanceBaseline | None:
        """Get current performance baseline."""
        return self.baseline

    def set_baseline(self, baseline: PerformanceBaseline) -> None:
        """Set performance baseline manually."""
        self.baseline = baseline


class FileBaselineStore(BaselineStore):
    """File-based baseline storage."""

    def __init__(self, directory: str = ".tantra/baselines"):
        """Initialize file-based baseline store.

        Args:
            directory: Directory path for storing baseline JSON files.
        """
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _get_path(self, agent_id: str) -> Path:
        """Get file path for agent baseline."""
        safe_id = agent_id.replace("/", "_").replace("\\", "_")
        return self.directory / f"{safe_id}.json"

    async def save(self, agent_id: str, baseline: PerformanceBaseline) -> None:
        """Save baseline to a JSON file."""
        path = self._get_path(agent_id)
        data = baseline.to_dict()
        data["agent_id"] = agent_id
        path.write_text(json.dumps(data, indent=2))

    async def load(self, agent_id: str) -> PerformanceBaseline | None:
        """Load baseline from a JSON file."""
        path = self._get_path(agent_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return PerformanceBaseline.from_dict(data)

    async def list_agents(self) -> list[str]:
        """List agent IDs from stored baseline files."""
        agents = []
        for path in self.directory.glob("*.json"):
            data = json.loads(path.read_text())
            if "agent_id" in data:
                agents.append(data["agent_id"])
        return agents


class PerformanceMonitor:
    """Monitors agent performance and detects degradation.

    Tracks metrics over time and compares against baseline.
    Can trigger callbacks when degradation is detected.

    Examples:
        ```python
        monitor = PerformanceMonitor(
            baseline=baseline,
            on_degradation=lambda m: alert_ops_team(m),
        )

        # After each agent run
        monitor.record_run(result.metadata)

        # Periodically check for degradation
        if monitor.is_degraded():
            trigger_rollback()
        ```
    """

    def __init__(
        self,
        baseline: PerformanceBaseline | None = None,
        thresholds: DegradationThresholds | None = None,
        window_size: int = 100,
        on_degradation: Callable[[str], None] | None = None,
    ):
        """Initialize monitor.

        Args:
            baseline: Performance baseline to compare against.
            thresholds: Degradation detection thresholds.
            window_size: Number of recent runs to track.
            on_degradation: Callback when degradation detected.
        """
        self.baseline = baseline
        self.thresholds = thresholds or DegradationThresholds()
        self.window_size = window_size
        self.on_degradation = on_degradation

        self._runs: list[RunMetadata] = []
        self._degradation_detected = False
        self._degradation_message: str | None = None

    def record_run(self, metadata: RunMetadata) -> None:
        """Record a completed run.

        Args:
            metadata: Run metadata from agent execution.
        """
        self._runs.append(metadata)

        # Keep only recent runs
        if len(self._runs) > self.window_size:
            self._runs = self._runs[-self.window_size :]

        # Check for degradation
        self._check_degradation()

    def _check_degradation(self) -> None:
        """Check current metrics against baseline."""
        if not self.baseline:
            return

        if len(self._runs) < self.thresholds.min_sample_size:
            return

        # Calculate current metrics
        total_cost = sum(r.estimated_cost for r in self._runs)
        total_latency = sum(r.duration_ms for r in self._runs)
        n = len(self._runs)

        avg_cost = total_cost / n
        avg_latency = total_latency / n

        # Check cost
        if self.baseline.avg_cost > 0:
            cost_increase = (avg_cost - self.baseline.avg_cost) / self.baseline.avg_cost
            if cost_increase > self.thresholds.max_cost_increase:
                self._trigger_degradation(f"Cost increased by {cost_increase:.1%} from baseline")
                return

        # Check latency
        if self.baseline.avg_latency_ms > 0:
            latency_increase = (
                avg_latency - self.baseline.avg_latency_ms
            ) / self.baseline.avg_latency_ms
            if latency_increase > self.thresholds.max_latency_increase:
                self._trigger_degradation(
                    f"Latency increased by {latency_increase:.1%} from baseline"
                )
                return

        # No degradation
        self._degradation_detected = False
        self._degradation_message = None

    def _trigger_degradation(self, message: str) -> None:
        """Trigger degradation alert."""
        if not self._degradation_detected:
            self._degradation_detected = True
            self._degradation_message = message
            if self.on_degradation:
                self.on_degradation(message)

    def is_degraded(self) -> bool:
        """Check if degradation has been detected."""
        return self._degradation_detected

    def get_degradation_message(self) -> str | None:
        """Get degradation message if detected."""
        return self._degradation_message

    def get_current_metrics(self) -> dict[str, float] | None:
        """Get current performance metrics.

        Returns:
            Dict with avg_cost, avg_tokens, avg_latency_ms, or None if no data.
        """
        if not self._runs:
            return None

        n = len(self._runs)
        return {
            "avg_cost": sum(r.estimated_cost for r in self._runs) / n,
            "avg_tokens": sum(r.total_tokens for r in self._runs) / n,
            "avg_latency_ms": sum(r.duration_ms for r in self._runs) / n,
            "sample_size": n,
        }

    def reset(self) -> None:
        """Reset monitoring state."""
        self._runs.clear()
        self._degradation_detected = False
        self._degradation_message = None


async def deploy_with_gate(
    agent: Agent,
    gate: DeploymentGate,
    version: str,
    deploy_fn: Callable[[Agent], None] | None = None,
    rollback_fn: Callable[[str], None] | None = None,
) -> DeploymentResult:
    """Deploy an agent through an evaluation gate.

    Convenience function that runs evaluation and handles deployment.

    Args:
        agent: Agent to deploy.
        gate: Deployment gate with evaluation suite.
        version: Version string.
        deploy_fn: Optional function to call on successful deployment.
        rollback_fn: Optional function to call if previous version needs rollback.

    Returns:
        DeploymentResult with status and metrics.

    Examples:
        ```python
        result = await deploy_with_gate(
            agent=my_agent,
            gate=my_gate,
            version="2.0.0",
            deploy_fn=lambda a: k8s_deploy(a),
            rollback_fn=lambda v: k8s_rollback(v),
        )
        ```
    """
    result = await gate.evaluate(agent, version)

    if result.can_deploy:
        if deploy_fn:
            deploy_fn(agent)
        gate.record_deployment(result)
    elif result.status == DeploymentStatus.DEGRADED and rollback_fn:
        # Get previous version from deployment history
        history = gate.get_deployment_history()
        if history:
            previous = history[-1]
            rollback_fn(previous.version)
            result.rolled_back_at = datetime.now(UTC)
            result.status = DeploymentStatus.ROLLED_BACK

    return result
