"""Base classes for evaluation framework.

Contains abstract base classes that users can extend for custom implementations:
- Matcher: Create custom test matchers
- BaselineStore: Store performance baselines in custom backends
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..types import RunResult
    from .suite import EvalResult


# ============================================================================
# Matcher Base Classes
# ============================================================================


class Matcher(ABC):
    """Base class for evaluation matchers.

    Matchers define conditions that must be met for a test to pass.
    They can check the output, trace, metadata, or any other aspect
    of an agent run.

    Examples:
        ```python
        class LengthMatcher(Matcher):
            def __init__(self, min_length: int):
                self.min_length = min_length

            @property
            def description(self) -> str:
                return f"output has at least {self.min_length} characters"

            def match(self, result: RunResult) -> MatchResult:
                passed = len(result.output) >= self.min_length
                return MatchResult(
                    passed=passed,
                    message=f"Output length: {len(result.output)}",
                    matcher_description=self.description,
                )
        ```
    """

    @abstractmethod
    def match(self, result: RunResult) -> MatchResult:
        """Check if the result matches the expected condition.

        Args:
            result: The RunResult from an agent run.

        Returns:
            MatchResult indicating success or failure with details.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this matcher checks."""
        pass


@dataclass
class MatchResult:
    """Result of a matcher check.

    Attributes:
        passed: Whether the matcher condition was satisfied.
        message: Human-readable description of the result.
        matcher_description: Description of the matcher that produced this result.
        details: Additional key-value details about the match.
    """

    passed: bool
    message: str
    matcher_description: str
    details: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Baseline Store Base Class
# ============================================================================


@dataclass
class PerformanceBaseline:
    """Baseline performance metrics for comparison.

    Attributes:
        pass_rate: Fraction of tests passed (0.0 to 1.0).
        avg_cost: Average cost per run in USD.
        avg_tokens: Average tokens per run.
        avg_latency_ms: Average latency per run in milliseconds.
        recorded_at: When this baseline was recorded.
        sample_size: Number of test runs used to compute the baseline.
    """

    pass_rate: float  # 0.0 to 1.0
    avg_cost: float
    avg_tokens: int
    avg_latency_ms: float
    recorded_at: datetime | None = None
    sample_size: int = 0

    def __post_init__(self):
        if self.recorded_at is None:
            self.recorded_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict with all baseline fields serialized.
        """
        return {
            "pass_rate": self.pass_rate,
            "avg_cost": self.avg_cost,
            "avg_tokens": self.avg_tokens,
            "avg_latency_ms": self.avg_latency_ms,
            "recorded_at": self.recorded_at.isoformat(),
            "sample_size": self.sample_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PerformanceBaseline:
        """Create from dictionary.

        Args:
            data: Dict with baseline fields as produced by ``to_dict``.

        Returns:
            A new PerformanceBaseline instance.
        """
        return cls(
            pass_rate=data["pass_rate"],
            avg_cost=data["avg_cost"],
            avg_tokens=data["avg_tokens"],
            avg_latency_ms=data["avg_latency_ms"],
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
            sample_size=data.get("sample_size", 0),
        )

    @classmethod
    def from_evaluation(cls, result: EvalResult) -> PerformanceBaseline:
        """Create baseline from evaluation result.

        Args:
            result: Evaluation result containing aggregated metrics.

        Returns:
            A new PerformanceBaseline derived from the evaluation metrics.
        """
        return cls(
            pass_rate=result.metrics.pass_rate,
            avg_cost=result.metrics.average_cost,
            avg_tokens=int(result.metrics.average_tokens),
            avg_latency_ms=result.metrics.average_duration_ms,
            sample_size=result.metrics.total_tests,
        )


class BaselineStore(ABC):
    """Abstract storage for performance baselines.

    Extend this class to store baselines in your preferred backend
    (Redis, PostgreSQL, S3, etc.).

    Examples:
        ```python
        class RedisBaselineStore(BaselineStore):
            def __init__(self, redis_client):
                self.redis = redis_client

            async def save(self, agent_id: str, baseline: PerformanceBaseline) -> None:
                key = f"tantra:baseline:{agent_id}"
                await self.redis.set(key, json.dumps(baseline.to_dict()))

            async def load(self, agent_id: str) -> PerformanceBaseline | None:
                key = f"tantra:baseline:{agent_id}"
                data = await self.redis.get(key)
                if data:
                    return PerformanceBaseline.from_dict(json.loads(data))
                return None

            async def list_agents(self) -> list[str]:
                keys = await self.redis.keys("tantra:baseline:*")
                return [k.split(":")[-1] for k in keys]
        ```
    """

    @abstractmethod
    async def save(self, agent_id: str, baseline: PerformanceBaseline) -> None:
        """Save baseline for an agent.

        Args:
            agent_id: Unique identifier for the agent.
            baseline: The performance baseline to persist.
        """
        pass

    @abstractmethod
    async def load(self, agent_id: str) -> PerformanceBaseline | None:
        """Load baseline for an agent.

        Args:
            agent_id: Unique identifier for the agent.

        Returns:
            The stored baseline, or None if not found.
        """
        pass

    @abstractmethod
    async def list_agents(self) -> list[str]:
        """List all agents with baselines.

        Returns:
            List of agent IDs that have stored baselines.
        """
        pass
