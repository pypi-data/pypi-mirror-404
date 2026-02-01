"""Evaluation and deployment components for Tantra.

Provides testing, evaluation suites, matchers, and deployment gating.

Example:
    from tantra.evaluation import (
        EvalCase, EvalSuite, contains, tool_called,
        DeploymentGate, deploy_with_gate,
    )

    # Create evaluation suite
    suite = EvalSuite()
    suite.add_test(EvalCase(
        input="Hello!",
        matchers=[contains("hello", case_sensitive=False)]
    ))

    # Run evaluation
    results = await suite.run(agent)
    print(f"Passed: {results.passed}/{results.metrics.total_tests}")

    # Deployment gating
    gate = DeploymentGate(suite=suite, min_pass_rate=0.95)
    result = await deploy_with_gate(agent, gate, version="1.0.0")
"""

# Base classes (for extension)
from .base import (
    BaselineStore,
    Matcher,
    MatchResult,
    PerformanceBaseline,
)

# Deployment
from .deployment import (
    DegradationThresholds,
    DeploymentGate,
    DeploymentResult,
    DeploymentStatus,
    FileBaselineStore,
    PerformanceMonitor,
    deploy_with_gate,
)

# Built-in matchers and convenience functions
from .matchers import (
    ContainsMatcher,
    CostUnderMatcher,
    CustomMatcher,
    JsonSchemaMatcher,
    JsonValidMatcher,
    MatchesRegexMatcher,
    NotContainsMatcher,
    TokensUnderMatcher,
    ToolCalledMatcher,
    ToolNotCalledMatcher,
    # Convenience functions
    contains,
    cost_under,
    custom,
    json_schema,
    json_valid,
    matches_regex,
    not_contains,
    tokens_under,
    tool_called,
    tool_not_called,
)

# Evaluation suite
from .suite import (
    EvalCase,
    EvalMetrics,
    EvalResult,
    EvalSuite,
    TestResult,
)

__all__ = [
    # Base classes
    "Matcher",
    "MatchResult",
    "BaselineStore",
    "PerformanceBaseline",
    # Built-in matchers
    "ContainsMatcher",
    "NotContainsMatcher",
    "MatchesRegexMatcher",
    "JsonValidMatcher",
    "JsonSchemaMatcher",
    "ToolCalledMatcher",
    "ToolNotCalledMatcher",
    "CostUnderMatcher",
    "TokensUnderMatcher",
    "CustomMatcher",
    # Convenience functions
    "contains",
    "not_contains",
    "matches_regex",
    "json_valid",
    "json_schema",
    "tool_called",
    "tool_not_called",
    "cost_under",
    "tokens_under",
    "custom",
    # Evaluation suite
    "EvalCase",
    "TestResult",
    "EvalMetrics",
    "EvalResult",
    "EvalSuite",
    # Deployment
    "DeploymentGate",
    "DeploymentResult",
    "DeploymentStatus",
    "DegradationThresholds",
    "FileBaselineStore",
    "PerformanceMonitor",
    "deploy_with_gate",
]
