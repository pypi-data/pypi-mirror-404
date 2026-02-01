"""Evaluation suite for testing agents.

Provides EvalCase, EvalSuite, and related classes for
running comprehensive tests against agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import BaseModel

from ..types import RunMetadata, RunResult
from .base import Matcher, MatchResult

if TYPE_CHECKING:
    from ..agent import Agent


@dataclass
class EvalCase:
    """A single test case for evaluating an agent.

    Attributes:
        input: The user input to send to the agent.
        matchers: List of matchers that must all pass.
        name: Optional name for this test case.
        description: Optional human-readable description.
        tags: Tags for filtering or grouping test cases.

    Examples:
        ```python
        test = EvalCase(
            name="weather_query",
            input="What's the weather in Tokyo?",
            matchers=[
                contains("Tokyo"),
                tool_called("get_weather"),
            ]
        )
        ```
    """

    input: str
    matchers: list[Matcher] = field(default_factory=list)
    name: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of running a single test case.

    Attributes:
        test_case: The test case that was run.
        passed: Whether all matchers passed.
        run_result: The agent's RunResult for this test.
        match_results: Individual results from each matcher.
        error: Exception if the agent run failed, else None.
    """

    test_case: EvalCase
    passed: bool
    run_result: RunResult
    match_results: list[MatchResult]
    error: Exception | None = None

    @property
    def failed_matchers(self) -> list[MatchResult]:
        """Get all failed match results."""
        return [m for m in self.match_results if not m.passed]


class EvalMetrics(BaseModel):
    """Aggregated metrics from an evaluation run.

    Attributes:
        total_tests: Total number of test cases executed.
        passed: Number of tests that passed.
        failed: Number of tests that failed.
        pass_rate: Fraction of tests passed (0.0 to 1.0).
        total_cost: Sum of estimated costs across all runs.
        total_tokens: Sum of tokens across all runs.
        average_cost: Mean cost per run in USD.
        average_tokens: Mean tokens per run.
        average_duration_ms: Mean duration per run in milliseconds.
    """

    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    total_cost: float
    total_tokens: int
    average_cost: float
    average_tokens: float
    average_duration_ms: float


@dataclass
class EvalResult:
    """Result of running an evaluation suite.

    Attributes:
        results: Individual test results.
        metrics: Aggregated metrics across all tests.
    """

    results: list[TestResult]
    metrics: EvalMetrics

    @property
    def passed(self) -> int:
        """Number of passed tests."""
        return self.metrics.passed

    @property
    def failed(self) -> int:
        """Number of failed tests."""
        return self.metrics.failed

    @property
    def all_passed(self) -> bool:
        """Whether all tests passed."""
        return self.metrics.failed == 0

    def get_failures(self) -> list[TestResult]:
        """Get all failed test results."""
        return [r for r in self.results if not r.passed]


class EvalSuite:
    """A collection of test cases for evaluating an agent.

    Examples:
        ```python
        suite = EvalSuite()
        suite.add_test(EvalCase(
            input="Hello!",
            matchers=[contains("hello", case_sensitive=False)]
        ))
        suite.add_test(EvalCase(
            input="What is 2+2?",
            matchers=[contains("4")]
        ))

        results = await suite.run(agent)
        print(f"Passed: {results.passed}/{results.metrics.total_tests}")
        ```
    """

    def __init__(self, name: str | None = None):
        """Initialize evaluation suite.

        Args:
            name: Optional name for the suite.
        """
        self.name = name
        self._tests: list[EvalCase] = []

    def add_test(self, test: EvalCase) -> None:
        """Add a test case to the suite.

        Args:
            test: The evaluation case to add.
        """
        self._tests.append(test)

    def add_tests(self, tests: list[EvalCase]) -> None:
        """Add multiple test cases.

        Args:
            tests: List of evaluation cases to add.
        """
        self._tests.extend(tests)

    async def run(self, agent: Agent) -> EvalResult:
        """Run all test cases against the agent.

        Args:
            agent: The agent to evaluate.

        Returns:
            EvalResult with all test results and metrics.
        """
        results: list[TestResult] = []

        for test in self._tests:
            result = await self._run_test(agent, test)
            results.append(result)

        metrics = self._calculate_metrics(results)
        return EvalResult(results=results, metrics=metrics)

    async def _run_test(self, agent: Agent, test: EvalCase) -> TestResult:
        """Run a single test case."""
        try:
            # Clear memory before each test for isolation
            agent.clear_memory()

            # Run the agent
            run_result = await agent.run(test.input)

            # Check all matchers
            match_results = [m.match(run_result) for m in test.matchers]

            # Test passes if all matchers pass
            passed = all(m.passed for m in match_results)

            return TestResult(
                test_case=test,
                passed=passed,
                run_result=run_result,
                match_results=match_results,
            )

        except Exception as e:
            # If agent run fails, test fails
            from uuid import uuid4

            return TestResult(
                test_case=test,
                passed=False,
                run_result=RunResult(
                    output="",
                    trace=[],
                    metadata=RunMetadata(run_id=uuid4()),
                ),
                match_results=[],
                error=e,
            )

    def _calculate_metrics(self, results: list[TestResult]) -> EvalMetrics:
        """Calculate aggregated metrics from results."""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        total_cost = sum(r.run_result.metadata.estimated_cost for r in results)
        total_tokens = sum(r.run_result.metadata.total_tokens for r in results)
        total_duration = sum(r.run_result.metadata.duration_ms for r in results)

        return EvalMetrics(
            total_tests=total,
            passed=passed,
            failed=failed,
            pass_rate=passed / total if total > 0 else 0.0,
            total_cost=total_cost,
            total_tokens=total_tokens,
            average_cost=total_cost / total if total > 0 else 0.0,
            average_tokens=total_tokens / total if total > 0 else 0.0,
            average_duration_ms=total_duration / total if total > 0 else 0.0,
        )

    @property
    def test_count(self) -> int:
        """Number of tests in the suite."""
        return len(self._tests)

    def __len__(self) -> int:
        """Return the number of tests in the suite."""
        return len(self._tests)
