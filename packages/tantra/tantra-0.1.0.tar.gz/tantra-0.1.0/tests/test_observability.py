"""Tests for observability components."""

from uuid import uuid4

from tantra import CostTracker, LogEntry, Logger, LogType


class TestLogEntry:
    """Tests for LogEntry model."""

    def test_create_log_entry(self):
        """Create a log entry."""
        run_id = uuid4()
        entry = LogEntry(
            run_id=run_id,
            type=LogType.PROMPT,
            data={"messages": [{"role": "user", "content": "Hello"}]},
            metadata={"extra": "info"},
        )

        assert entry.run_id == run_id
        assert entry.type == LogType.PROMPT
        assert "messages" in entry.data
        assert entry.timestamp is not None

    def test_log_types(self):
        """All log types exist."""
        assert LogType.PROMPT
        assert LogType.LLM_RESPONSE
        assert LogType.TOOL_CALL
        assert LogType.TOOL_RESULT
        assert LogType.FINAL_RESPONSE
        assert LogType.ERROR


class TestLogger:
    """Tests for Logger class."""

    def test_create_logger(self):
        """Create logger with run_id."""
        run_id = uuid4()
        logger = Logger(run_id=run_id)

        assert logger.run_id == run_id
        assert len(logger.entries) == 0

    def test_log_prompt(self):
        """Log a prompt."""
        logger = Logger(run_id=uuid4())
        messages = [{"role": "user", "content": "Hello"}]

        entry = logger.log_prompt(messages)

        assert entry.type == LogType.PROMPT
        assert entry.data["messages"] == messages
        assert len(logger.entries) == 1

    def test_log_llm_response(self):
        """Log an LLM response."""
        logger = Logger(run_id=uuid4())

        entry = logger.log_llm_response(
            content="Hello!",
            tool_calls=None,
            prompt_tokens=10,
            completion_tokens=5,
        )

        assert entry.type == LogType.LLM_RESPONSE
        assert entry.data["content"] == "Hello!"
        assert entry.metadata["prompt_tokens"] == 10
        assert entry.metadata["completion_tokens"] == 5

    def test_log_tool_call(self):
        """Log a tool call."""
        logger = Logger(run_id=uuid4())

        entry = logger.log_tool_call("get_weather", {"city": "Tokyo"})

        assert entry.type == LogType.TOOL_CALL
        assert entry.data["tool_name"] == "get_weather"
        assert entry.data["arguments"] == {"city": "Tokyo"}

    def test_log_tool_result(self):
        """Log a tool result."""
        logger = Logger(run_id=uuid4())

        entry = logger.log_tool_result("get_weather", "Sunny", 123.5)

        assert entry.type == LogType.TOOL_RESULT
        assert entry.data["tool_name"] == "get_weather"
        assert entry.data["result"] == "Sunny"
        assert entry.metadata["duration_ms"] == 123.5

    def test_log_final_response(self):
        """Log final response."""
        logger = Logger(run_id=uuid4())

        entry = logger.log_final_response("Final answer")

        assert entry.type == LogType.FINAL_RESPONSE
        assert entry.data["output"] == "Final answer"

    def test_log_error(self):
        """Log an error."""
        logger = Logger(run_id=uuid4())

        try:
            raise ValueError("Test error")
        except Exception as e:
            entry = logger.log_error(e, context="test")

        assert entry.type == LogType.ERROR
        assert "Test error" in entry.data["error_message"]
        assert entry.data["context"] == "test"

    def test_callback_on_log(self):
        """Callback is called for each log entry."""
        captured = []

        def callback(entry):
            captured.append(entry)

        logger = Logger(run_id=uuid4(), callback=callback)
        logger.log_prompt([])
        logger.log_final_response("Done")

        assert len(captured) == 2

    def test_get_duration_ms(self):
        """Get duration since start."""
        logger = Logger(run_id=uuid4())
        logger.start_run()

        # Small delay
        import time

        time.sleep(0.01)

        duration = logger.get_duration_ms()
        assert duration > 0


class TestCostTracker:
    """Tests for CostTracker."""

    def test_create_tracker(self):
        """Create cost tracker."""
        tracker = CostTracker(model="gpt-4o")

        assert tracker.model == "gpt-4o"
        assert tracker.total_tokens == 0

    def test_add_tokens(self):
        """Track token usage."""
        tracker = CostTracker(model="gpt-4o")

        tracker.add_tokens(prompt_tokens=100, completion_tokens=50)

        assert tracker.prompt_tokens == 100
        assert tracker.completion_tokens == 50
        assert tracker.total_tokens == 150

    def test_add_tokens_multiple(self):
        """Track tokens across multiple calls."""
        tracker = CostTracker(model="gpt-4o")

        tracker.add_tokens(100, 50)
        tracker.add_tokens(200, 100)

        assert tracker.prompt_tokens == 300
        assert tracker.completion_tokens == 150
        assert tracker.total_tokens == 450

    def test_estimated_cost(self):
        """Calculate estimated cost."""
        tracker = CostTracker(model="gpt-4o")
        tracker.add_tokens(1000, 500)

        cost = tracker.estimated_cost
        assert cost > 0

    def test_cost_varies_by_model(self):
        """Different models have different costs."""
        tracker_4o = CostTracker(model="gpt-4o")
        tracker_4o.add_tokens(1000, 500)

        tracker_mini = CostTracker(model="gpt-4o-mini")
        tracker_mini.add_tokens(1000, 500)

        # gpt-4o should be more expensive than gpt-4o-mini
        assert tracker_4o.estimated_cost > tracker_mini.estimated_cost

    def test_unknown_model_default_cost(self):
        """Unknown model gets default cost."""
        tracker = CostTracker(model="unknown-model")
        tracker.add_tokens(1000, 500)

        cost = tracker.estimated_cost
        assert cost > 0  # Should use default rates
