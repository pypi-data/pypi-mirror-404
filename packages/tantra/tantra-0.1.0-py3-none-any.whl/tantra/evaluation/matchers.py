"""Built-in matchers for evaluation framework.

Provides common matchers for testing agent output, tool usage,
cost, and token consumption.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .base import Matcher, MatchResult

if TYPE_CHECKING:
    from ..types import RunResult

from ..types import LogType

# ============================================================================
# Built-in Matchers
# ============================================================================


class ContainsMatcher(Matcher):
    """Check if the output contains a substring."""

    def __init__(self, text: str, case_sensitive: bool = True):
        """Initialize ContainsMatcher.

        Args:
            text: Substring to look for.
            case_sensitive: Whether comparison is case-sensitive.
        """
        self.text = text
        self.case_sensitive = case_sensitive

    @property
    def description(self) -> str:
        return f"output contains '{self.text}'"

    def match(self, result: RunResult) -> MatchResult:
        """Check whether the output contains the target substring."""
        output = result.output
        text = self.text

        if not self.case_sensitive:
            output = output.lower()
            text = text.lower()

        passed = text in output
        return MatchResult(
            passed=passed,
            message=f"Output {'contains' if passed else 'does not contain'} '{self.text}'",
            matcher_description=self.description,
        )


class NotContainsMatcher(Matcher):
    """Check if the output does NOT contain a substring."""

    def __init__(self, text: str, case_sensitive: bool = True):
        """Initialize NotContainsMatcher.

        Args:
            text: Substring that must be absent.
            case_sensitive: Whether comparison is case-sensitive.
        """
        self.text = text
        self.case_sensitive = case_sensitive

    @property
    def description(self) -> str:
        return f"output does not contain '{self.text}'"

    def match(self, result: RunResult) -> MatchResult:
        """Check that the output does not contain the target substring."""
        output = result.output
        text = self.text

        if not self.case_sensitive:
            output = output.lower()
            text = text.lower()

        passed = text not in output
        return MatchResult(
            passed=passed,
            message=f"Output {'does not contain' if passed else 'contains'} '{self.text}'",
            matcher_description=self.description,
        )


class MatchesRegexMatcher(Matcher):
    """Check if the output matches a regex pattern."""

    def __init__(self, pattern: str, flags: int = 0):
        """Initialize MatchesRegexMatcher.

        Args:
            pattern: Regular expression pattern string.
            flags: Regex flags (e.g. ``re.IGNORECASE``).
        """
        self.pattern = pattern
        self.flags = flags
        self._compiled = re.compile(pattern, flags)

    @property
    def description(self) -> str:
        return f"output matches regex '{self.pattern}'"

    def match(self, result: RunResult) -> MatchResult:
        """Search the output for a regex match."""
        match = self._compiled.search(result.output)
        passed = match is not None
        return MatchResult(
            passed=passed,
            message=f"Output {'matches' if passed else 'does not match'} pattern",
            matcher_description=self.description,
            details={"matched_text": match.group() if match else None},
        )


class JsonValidMatcher(Matcher):
    """Check if the output is valid JSON."""

    @property
    def description(self) -> str:
        return "output is valid JSON"

    def match(self, result: RunResult) -> MatchResult:
        try:
            json.loads(result.output)
            return MatchResult(
                passed=True,
                message="Output is valid JSON",
                matcher_description=self.description,
            )
        except json.JSONDecodeError as e:
            return MatchResult(
                passed=False,
                message=f"Output is not valid JSON: {e}",
                matcher_description=self.description,
            )


class JsonSchemaMatcher(Matcher):
    """Check if the output matches a JSON schema."""

    def __init__(self, schema: dict[str, Any]):
        """Initialize JsonSchemaMatcher.

        Args:
            schema: JSON Schema dict to validate against.
        """
        self.schema = schema

    @property
    def description(self) -> str:
        return "output matches JSON schema"

    def match(self, result: RunResult) -> MatchResult:
        """Parse the output as JSON and validate it against the schema."""
        try:
            data = json.loads(result.output)
        except json.JSONDecodeError as e:
            return MatchResult(
                passed=False,
                message=f"Output is not valid JSON: {e}",
                matcher_description=self.description,
            )

        # Simple schema validation (for MVP - consider jsonschema package for full validation)
        errors = self._validate_schema(data, self.schema)
        passed = len(errors) == 0

        return MatchResult(
            passed=passed,
            message="Output matches schema" if passed else f"Schema validation failed: {errors}",
            matcher_description=self.description,
            details={"errors": errors},
        )

    def _validate_schema(self, data: Any, schema: dict[str, Any], path: str = "") -> list[str]:
        """Simple schema validation."""
        errors = []

        expected_type = schema.get("type")
        if expected_type:
            type_map = {
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict,
                "null": type(None),
            }
            expected = type_map.get(expected_type)
            if expected and not isinstance(data, expected):
                errors.append(
                    f"{path or 'root'}: expected {expected_type}, got {type(data).__name__}"
                )
                return errors

        if expected_type == "object" and isinstance(data, dict):
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for prop in required:
                if prop not in data:
                    errors.append(f"{path}.{prop}: required property missing")

            for prop, prop_schema in properties.items():
                if prop in data:
                    errors.extend(self._validate_schema(data[prop], prop_schema, f"{path}.{prop}"))

        if expected_type == "array" and isinstance(data, list):
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(data):
                    errors.extend(self._validate_schema(item, items_schema, f"{path}[{i}]"))

        return errors


class ToolCalledMatcher(Matcher):
    """Check if a specific tool was called during execution."""

    def __init__(self, tool_name: str, min_times: int = 1, max_times: int | None = None):
        """Initialize ToolCalledMatcher.

        Args:
            tool_name: Name of the tool to check for.
            min_times: Minimum required call count.
            max_times: Maximum allowed call count (None for unlimited).
        """
        self.tool_name = tool_name
        self.min_times = min_times
        self.max_times = max_times

    @property
    def description(self) -> str:
        if self.max_times is None:
            return f"tool '{self.tool_name}' called at least {self.min_times} time(s)"
        return f"tool '{self.tool_name}' called {self.min_times}-{self.max_times} time(s)"

    def match(self, result: RunResult) -> MatchResult:
        """Count tool calls in the trace and check against bounds."""
        call_count = sum(
            1
            for entry in result.trace
            if entry.type == LogType.TOOL_CALL and entry.data.get("tool_name") == self.tool_name
        )

        passed = call_count >= self.min_times
        if self.max_times is not None:
            passed = passed and call_count <= self.max_times

        return MatchResult(
            passed=passed,
            message=f"Tool '{self.tool_name}' was called {call_count} time(s)",
            matcher_description=self.description,
            details={"call_count": call_count},
        )


class ToolNotCalledMatcher(Matcher):
    """Check that a specific tool was NOT called."""

    def __init__(self, tool_name: str):
        """Initialize ToolNotCalledMatcher.

        Args:
            tool_name: Name of the tool that must not appear.
        """
        self.tool_name = tool_name

    @property
    def description(self) -> str:
        return f"tool '{self.tool_name}' was not called"

    def match(self, result: RunResult) -> MatchResult:
        """Verify the named tool does not appear in the trace."""
        was_called = any(
            entry.type == LogType.TOOL_CALL and entry.data.get("tool_name") == self.tool_name
            for entry in result.trace
        )

        return MatchResult(
            passed=not was_called,
            message=f"Tool '{self.tool_name}' was {'called' if was_called else 'not called'}",
            matcher_description=self.description,
        )


class CostUnderMatcher(Matcher):
    """Check that the estimated cost is under a threshold."""

    def __init__(self, max_cost: float):
        """Initialize CostUnderMatcher.

        Args:
            max_cost: Maximum allowed cost in USD.
        """
        self.max_cost = max_cost

    @property
    def description(self) -> str:
        return f"cost under ${self.max_cost:.4f}"

    def match(self, result: RunResult) -> MatchResult:
        """Compare the run's estimated cost against the threshold."""
        cost = result.metadata.estimated_cost
        passed = cost <= self.max_cost

        return MatchResult(
            passed=passed,
            message=f"Cost ${cost:.4f} is {'under' if passed else 'over'} ${self.max_cost:.4f}",
            matcher_description=self.description,
            details={"actual_cost": cost},
        )


class TokensUnderMatcher(Matcher):
    """Check that total tokens used is under a threshold."""

    def __init__(self, max_tokens: int):
        """Initialize TokensUnderMatcher.

        Args:
            max_tokens: Maximum allowed total token count.
        """
        self.max_tokens = max_tokens

    @property
    def description(self) -> str:
        return f"tokens under {self.max_tokens}"

    def match(self, result: RunResult) -> MatchResult:
        """Compare the run's total tokens against the threshold."""
        tokens = result.metadata.total_tokens
        passed = tokens <= self.max_tokens

        return MatchResult(
            passed=passed,
            message=f"Used {tokens} tokens ({'under' if passed else 'over'} {self.max_tokens})",
            matcher_description=self.description,
            details={"actual_tokens": tokens},
        )


class CustomMatcher(Matcher):
    """Create a custom matcher from a function."""

    def __init__(self, func: Callable[[RunResult], bool], description: str):
        """Initialize CustomMatcher.

        Args:
            func: Function that takes a RunResult and returns True if matched.
            description: Human-readable description for this matcher.
        """
        self._func = func
        self._description = description

    @property
    def description(self) -> str:
        return self._description

    def match(self, result: RunResult) -> MatchResult:
        """Invoke the custom function and wrap exceptions as failures."""
        try:
            passed = self._func(result)
            return MatchResult(
                passed=passed,
                message=f"Custom check {'passed' if passed else 'failed'}",
                matcher_description=self.description,
            )
        except Exception as e:
            return MatchResult(
                passed=False,
                message=f"Custom check raised exception: {e}",
                matcher_description=self.description,
            )


# ============================================================================
# Convenience functions for creating matchers
# ============================================================================


def contains(text: str, case_sensitive: bool = True) -> ContainsMatcher:
    """Create a matcher that checks if output contains text.

    Args:
        text: Substring to look for.
        case_sensitive: Whether comparison is case-sensitive.

    Returns:
        A ContainsMatcher instance.
    """
    return ContainsMatcher(text, case_sensitive)


def not_contains(text: str, case_sensitive: bool = True) -> NotContainsMatcher:
    """Create a matcher that checks if output does NOT contain text.

    Args:
        text: Substring that must be absent.
        case_sensitive: Whether comparison is case-sensitive.

    Returns:
        A NotContainsMatcher instance.
    """
    return NotContainsMatcher(text, case_sensitive)


def matches_regex(pattern: str, flags: int = 0) -> MatchesRegexMatcher:
    """Create a matcher that checks if output matches a regex.

    Args:
        pattern: Regular expression pattern string.
        flags: Regex flags (e.g. ``re.IGNORECASE``).

    Returns:
        A MatchesRegexMatcher instance.
    """
    return MatchesRegexMatcher(pattern, flags)


def json_valid() -> JsonValidMatcher:
    """Create a matcher that checks if output is valid JSON.

    Returns:
        A JsonValidMatcher instance.
    """
    return JsonValidMatcher()


def json_schema(schema: dict[str, Any]) -> JsonSchemaMatcher:
    """Create a matcher that checks if output matches a JSON schema.

    Args:
        schema: JSON Schema dict to validate against.

    Returns:
        A JsonSchemaMatcher instance.
    """
    return JsonSchemaMatcher(schema)


def tool_called(name: str, min_times: int = 1, max_times: int | None = None) -> ToolCalledMatcher:
    """Create a matcher that checks if a tool was called.

    Args:
        name: Name of the tool to check for.
        min_times: Minimum required call count.
        max_times: Maximum allowed call count (None for unlimited).

    Returns:
        A ToolCalledMatcher instance.
    """
    return ToolCalledMatcher(name, min_times, max_times)


def tool_not_called(name: str) -> ToolNotCalledMatcher:
    """Create a matcher that checks if a tool was NOT called.

    Args:
        name: Name of the tool that must not appear.

    Returns:
        A ToolNotCalledMatcher instance.
    """
    return ToolNotCalledMatcher(name)


def cost_under(max_cost: float) -> CostUnderMatcher:
    """Create a matcher that checks if cost is under a threshold.

    Args:
        max_cost: Maximum allowed cost in USD.

    Returns:
        A CostUnderMatcher instance.
    """
    return CostUnderMatcher(max_cost)


def tokens_under(max_tokens: int) -> TokensUnderMatcher:
    """Create a matcher that checks if tokens are under a threshold.

    Args:
        max_tokens: Maximum allowed total token count.

    Returns:
        A TokensUnderMatcher instance.
    """
    return TokensUnderMatcher(max_tokens)


def custom(func: Callable[[RunResult], bool], description: str) -> CustomMatcher:
    """Create a custom matcher from a function.

    Args:
        func: Function that takes a RunResult and returns True if matched.
        description: Human-readable description for the matcher.

    Returns:
        A CustomMatcher instance.
    """
    return CustomMatcher(func, description)
