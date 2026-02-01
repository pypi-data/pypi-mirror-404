"""Tests for evaluation framework."""

from uuid import uuid4

import pytest
from conftest import MockProvider

from tantra import (
    Agent,
    EvalCase,
    EvalSuite,
    LogType,
    RunMetadata,
    RunResult,
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


class TestMatchers:
    """Tests for built-in matchers."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample RunResult for testing."""
        from tantra.types import LogEntry

        trace = [
            LogEntry(
                run_id=uuid4(),
                type=LogType.TOOL_CALL,
                data={"tool_name": "get_weather", "arguments": {"city": "Tokyo"}},
            ),
            LogEntry(
                run_id=uuid4(),
                type=LogType.TOOL_RESULT,
                data={"tool_name": "get_weather", "result": "Sunny"},
            ),
            LogEntry(
                run_id=uuid4(),
                type=LogType.FINAL_RESPONSE,
                data={"response": "The weather in Tokyo is sunny."},
            ),
        ]

        return RunResult(
            output="The weather in Tokyo is sunny.",
            trace=trace,
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=150,
                prompt_tokens=100,
                completion_tokens=50,
                estimated_cost=0.005,
                duration_ms=1234.5,
                tool_calls_count=1,
            ),
        )

    def test_contains_match(self, sample_result):
        """contains matcher finds substring."""
        matcher = contains("Tokyo")
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_contains_no_match(self, sample_result):
        """contains matcher fails when substring missing."""
        matcher = contains("Paris")
        result = matcher.match(sample_result)

        assert result.passed is False
        assert "Paris" in result.message

    def test_contains_case_insensitive(self, sample_result):
        """contains matcher with case insensitive option."""
        matcher = contains("TOKYO", case_sensitive=False)
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_not_contains_match(self, sample_result):
        """not_contains passes when substring missing."""
        matcher = not_contains("Paris")
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_not_contains_no_match(self, sample_result):
        """not_contains fails when substring present."""
        matcher = not_contains("Tokyo")
        result = matcher.match(sample_result)

        assert result.passed is False

    def test_matches_regex(self, sample_result):
        """matches_regex finds pattern."""
        matcher = matches_regex(r"weather.*sunny", flags=2)  # re.IGNORECASE
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_matches_regex_no_match(self, sample_result):
        """matches_regex fails when pattern not found."""
        matcher = matches_regex(r"rainy|cloudy")
        result = matcher.match(sample_result)

        assert result.passed is False

    def test_json_valid_pass(self):
        """json_valid passes for valid JSON."""
        result = RunResult(
            output='{"key": "value", "number": 42}',
            trace=[],
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5,
                estimated_cost=0.001,
                duration_ms=100,
                tool_calls_count=0,
            ),
        )

        matcher = json_valid()
        match_result = matcher.match(result)

        assert match_result.passed is True

    def test_json_valid_fail(self):
        """json_valid fails for invalid JSON."""
        result = RunResult(
            output="This is not JSON",
            trace=[],
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5,
                estimated_cost=0.001,
                duration_ms=100,
                tool_calls_count=0,
            ),
        )

        matcher = json_valid()
        match_result = matcher.match(result)

        assert match_result.passed is False

    def test_json_schema_pass(self):
        """json_schema validates against schema."""
        result = RunResult(
            output='{"name": "John", "age": 30}',
            trace=[],
            metadata=RunMetadata(
                run_id=uuid4(),
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5,
                estimated_cost=0.001,
                duration_ms=100,
                tool_calls_count=0,
            ),
        )

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
        }

        matcher = json_schema(schema)
        match_result = matcher.match(result)

        assert match_result.passed is True

    def test_tool_called_pass(self, sample_result):
        """tool_called passes when tool was called."""
        matcher = tool_called("get_weather")
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_tool_called_fail(self, sample_result):
        """tool_called fails when tool was not called."""
        matcher = tool_called("send_email")
        result = matcher.match(sample_result)

        assert result.passed is False

    def test_tool_not_called_pass(self, sample_result):
        """tool_not_called passes when tool was not called."""
        matcher = tool_not_called("send_email")
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_tool_not_called_fail(self, sample_result):
        """tool_not_called fails when tool was called."""
        matcher = tool_not_called("get_weather")
        result = matcher.match(sample_result)

        assert result.passed is False

    def test_cost_under_pass(self, sample_result):
        """cost_under passes when cost is below threshold."""
        matcher = cost_under(0.01)
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_cost_under_fail(self, sample_result):
        """cost_under fails when cost exceeds threshold."""
        matcher = cost_under(0.001)
        result = matcher.match(sample_result)

        assert result.passed is False

    def test_tokens_under_pass(self, sample_result):
        """tokens_under passes when tokens below threshold."""
        matcher = tokens_under(200)
        result = matcher.match(sample_result)

        assert result.passed is True

    def test_tokens_under_fail(self, sample_result):
        """tokens_under fails when tokens exceed threshold."""
        matcher = tokens_under(100)
        result = matcher.match(sample_result)

        assert result.passed is False

    def test_custom_matcher(self, sample_result):
        """custom matcher runs user function."""

        def check_length(result):
            return len(result.output) > 10

        matcher = custom(check_length, "Output should be longer than 10 chars")
        match_result = matcher.match(sample_result)

        assert match_result.passed is True


class TestEvalCaseModel:
    """Tests for EvalCase."""

    def test_create_test_case(self):
        """Create a test case."""

        test = EvalCase(
            input="What's the weather?",
            matchers=[contains("sunny")],
        )

        assert test.input == "What's the weather?"
        assert len(test.matchers) == 1

    def test_test_case_with_name(self):
        """Test case with name."""

        test = EvalCase(
            name="weather_test",
            input="What's the weather?",
            matchers=[contains("weather")],
        )

        assert test.name == "weather_test"


class TestEvalSuiteClass:
    """Tests for EvalSuite."""

    def test_create_suite(self):
        """Create evaluation suite."""

        suite = EvalSuite()
        assert len(suite._tests) == 0

    def test_add_test(self):
        """Add test to suite."""

        suite = EvalSuite()
        test = EvalCase(input="Hello", matchers=[contains("hi")])

        suite.add_test(test)

        assert len(suite._tests) == 1

    @pytest.mark.asyncio
    async def test_run_suite(self):
        """Run evaluation suite."""

        provider = MockProvider(responses=["Hello, world!"])
        agent = Agent(provider)

        suite = EvalSuite()
        suite.add_test(EvalCase(input="Hi", matchers=[contains("Hello")]))
        suite.add_test(EvalCase(input="Hi", matchers=[contains("world")]))

        results = await suite.run(agent)

        assert results.metrics.total_tests == 2
        assert results.passed == 2
        assert results.failed == 0

    @pytest.mark.asyncio
    async def test_run_suite_with_failures(self):
        """Run suite with some failures."""

        provider = MockProvider(responses=["Hello"])
        agent = Agent(provider)

        suite = EvalSuite()
        suite.add_test(EvalCase(input="Hi", matchers=[contains("Hello")]))  # Pass
        suite.add_test(EvalCase(input="Hi", matchers=[contains("Goodbye")]))  # Fail

        results = await suite.run(agent)

        assert results.metrics.total_tests == 2
        assert results.passed == 1
        assert results.failed == 1

    @pytest.mark.asyncio
    async def test_run_suite_multiple_matchers(self):
        """Test case with multiple matchers."""

        provider = MockProvider(responses=["Hello, world!"])
        agent = Agent(provider)

        suite = EvalSuite()
        suite.add_test(
            EvalCase(
                input="Hi",
                matchers=[
                    contains("Hello"),
                    contains("world"),
                    not_contains("goodbye"),
                ],
            )
        )

        results = await suite.run(agent)

        assert results.passed == 1
        assert results.failed == 0

    def test_suite_metrics(self):
        """Suite calculates metrics."""

        suite = EvalSuite()
        suite.add_test(EvalCase(input="Test 1", matchers=[contains("a")]))
        suite.add_test(EvalCase(input="Test 2", matchers=[contains("b")]))

        # Before running, check test count
        assert len(suite._tests) == 2
