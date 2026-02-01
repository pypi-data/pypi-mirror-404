"""Tests for Retry and Recovery."""

import asyncio

import pytest

from tantra import (
    BackoffStrategy,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    LoggingRetryCallback,
    ProviderError,
    RetryableError,
    RetryCallback,
    RetryPolicy,
    retry_async,
    retry_sync,
    with_retry,
)

# =============================================================================
# RetryPolicy Tests
# =============================================================================


class TestRetryPolicy:
    """Tests for RetryPolicy."""

    def test_default_policy(self):
        """Default policy has sensible defaults."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.backoff == BackoffStrategy.EXPONENTIAL_JITTER
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0

    def test_constant_backoff(self):
        """Constant backoff returns same delay."""
        policy = RetryPolicy(
            backoff=BackoffStrategy.CONSTANT,
            base_delay=2.0,
        )
        assert policy.calculate_delay(0) == 2.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(5) == 2.0

    def test_linear_backoff(self):
        """Linear backoff increases linearly."""
        policy = RetryPolicy(
            backoff=BackoffStrategy.LINEAR,
            base_delay=1.0,
        )
        assert policy.calculate_delay(0) == 1.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 3.0

    def test_exponential_backoff(self):
        """Exponential backoff doubles each time."""
        policy = RetryPolicy(
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=1.0,
        )
        assert policy.calculate_delay(0) == 1.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 4.0
        assert policy.calculate_delay(3) == 8.0

    def test_max_delay_cap(self):
        """Delay is capped at max_delay."""
        policy = RetryPolicy(
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=5.0,
        )
        assert policy.calculate_delay(10) == 5.0

    def test_exponential_jitter(self):
        """Exponential jitter adds randomness."""
        policy = RetryPolicy(
            backoff=BackoffStrategy.EXPONENTIAL_JITTER,
            base_delay=1.0,
            jitter_factor=0.5,
        )
        # Should be between base and base * (1 + jitter)
        delay = policy.calculate_delay(0)
        assert 1.0 <= delay <= 1.5

    def test_is_retryable_provider_error(self):
        """ProviderError is retryable by default."""
        policy = RetryPolicy()
        assert policy.is_retryable(ProviderError("test"))

    def test_is_retryable_retryable_error(self):
        """RetryableError is retryable."""
        policy = RetryPolicy()
        assert policy.is_retryable(RetryableError("test"))

    def test_is_retryable_connection_error(self):
        """ConnectionError is retryable."""
        policy = RetryPolicy()
        assert policy.is_retryable(ConnectionError("test"))

    def test_is_retryable_timeout_error(self):
        """TimeoutError is retryable."""
        policy = RetryPolicy()
        assert policy.is_retryable(TimeoutError("test"))

    def test_is_not_retryable_value_error(self):
        """ValueError is not retryable by default."""
        policy = RetryPolicy()
        assert not policy.is_retryable(ValueError("test"))

    def test_custom_retryable_exceptions(self):
        """Can specify custom retryable exceptions."""
        policy = RetryPolicy(
            retryable_exceptions=(ValueError, KeyError),
        )
        assert policy.is_retryable(ValueError("test"))
        assert policy.is_retryable(KeyError("test"))
        assert not policy.is_retryable(TypeError("test"))


# =============================================================================
# Retry Function Tests
# =============================================================================


class TestRetryAsync:
    """Tests for retry_async function."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """Succeeds on first try without retry."""
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(succeed)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Succeeds after retries."""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("temporary failure")
            return "success"

        policy = RetryPolicy(max_retries=5, base_delay=0.01)
        result = await retry_async(fail_then_succeed, policy=policy)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self):
        """Raises after exhausting retries."""
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise RetryableError("always fails")

        policy = RetryPolicy(max_retries=3, base_delay=0.01)

        with pytest.raises(RetryableError):
            await retry_async(always_fail, policy=policy)

        assert call_count == 4  # 1 initial + 3 retries

    @pytest.mark.asyncio
    async def test_no_retry_non_retryable(self):
        """Does not retry non-retryable errors."""
        call_count = 0

        async def fail_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        policy = RetryPolicy(max_retries=3)

        with pytest.raises(ValueError):
            await retry_async(fail_with_value_error, policy=policy)

        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_callback_on_retry(self):
        """Callback is called on retry."""
        retries = []

        class TrackingCallback(RetryCallback):
            def on_retry(self, attempt, error, delay):
                retries.append((attempt, str(error)))

            def on_success(self, attempt, result):
                pass

            def on_failure(self, attempts, error):
                pass

        call_count = 0

        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("fail")
            return "ok"

        policy = RetryPolicy(max_retries=5, base_delay=0.01)
        await retry_async(fail_twice, policy=policy, callback=TrackingCallback())

        assert len(retries) == 2
        assert retries[0][0] == 0
        assert retries[1][0] == 1

    @pytest.mark.asyncio
    async def test_callback_on_success(self):
        """Callback is called on success."""
        success_info = {}

        class TrackingCallback(RetryCallback):
            def on_retry(self, attempt, error, delay):
                pass

            def on_success(self, attempt, result):
                success_info["attempt"] = attempt
                success_info["result"] = result

            def on_failure(self, attempts, error):
                pass

        async def succeed():
            return "done"

        await retry_async(succeed, callback=TrackingCallback())

        assert success_info["attempt"] == 0
        assert success_info["result"] == "done"

    @pytest.mark.asyncio
    async def test_callback_on_failure(self):
        """Callback is called on final failure."""
        failure_info = {}

        class TrackingCallback(RetryCallback):
            def on_retry(self, attempt, error, delay):
                pass

            def on_success(self, attempt, result):
                pass

            def on_failure(self, attempts, error):
                failure_info["attempts"] = attempts
                failure_info["error"] = str(error)

        async def always_fail():
            raise RetryableError("nope")

        policy = RetryPolicy(max_retries=2, base_delay=0.01)

        with pytest.raises(RetryableError):
            await retry_async(always_fail, policy=policy, callback=TrackingCallback())

        assert failure_info["attempts"] == 3
        assert "nope" in failure_info["error"]


class TestRetrySync:
    """Tests for retry_sync function."""

    def test_success_first_try(self):
        """Succeeds on first try."""
        call_count = 0

        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry_sync(succeed)
        assert result == "success"
        assert call_count == 1

    def test_success_after_retry(self):
        """Succeeds after retries."""
        call_count = 0

        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("fail")
            return "ok"

        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        result = retry_sync(fail_then_succeed, policy=policy)
        assert result == "ok"
        assert call_count == 2


class TestWithRetryDecorator:
    """Tests for @with_retry decorator."""

    @pytest.mark.asyncio
    async def test_async_decorator(self):
        """Decorator works with async functions."""
        call_count = 0

        @with_retry(RetryPolicy(max_retries=3, base_delay=0.01))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("fail")
            return "ok"

        result = await flaky()
        assert result == "ok"
        assert call_count == 2

    def test_sync_decorator(self):
        """Decorator works with sync functions."""
        call_count = 0

        @with_retry(RetryPolicy(max_retries=3, base_delay=0.01))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("fail")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert call_count == 2


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.mark.asyncio
    async def test_starts_closed(self):
        """Circuit starts in closed state."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed

    @pytest.mark.asyncio
    async def test_stays_closed_on_success(self):
        """Circuit stays closed on success."""
        breaker = CircuitBreaker()

        async with breaker:
            pass  # Success

        assert breaker.is_closed

    @pytest.mark.asyncio
    async def test_opens_after_failures(self):
        """Circuit opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        for _ in range(3):
            try:
                async with breaker:
                    raise ValueError("fail")
            except ValueError:
                pass

        assert breaker.is_open

    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        """Circuit rejects requests when open."""
        breaker = CircuitBreaker()
        breaker.force_open()

        with pytest.raises(CircuitOpenError):
            async with breaker:
                pass

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self):
        """Circuit goes half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,  # 100ms
        )
        breaker = CircuitBreaker(config)

        # Trigger open
        try:
            async with breaker:
                raise ValueError("fail")
        except ValueError:
            pass

        assert breaker.is_open

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Should be able to try again (half-open)
        try:
            async with breaker:
                pass  # Success
        except CircuitOpenError:
            pytest.fail("Should have allowed request in half-open")

    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self):
        """Circuit closes after successes in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.05,
            success_threshold=2,
        )
        breaker = CircuitBreaker(config)

        # Open the circuit
        try:
            async with breaker:
                raise ValueError("fail")
        except ValueError:
            pass

        # Wait for half-open
        await asyncio.sleep(0.1)

        # Succeed twice
        for _ in range(2):
            async with breaker:
                pass

        assert breaker.is_closed

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self):
        """Circuit reopens on failure in half-open."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.05,
        )
        breaker = CircuitBreaker(config)

        # Open the circuit
        try:
            async with breaker:
                raise ValueError("fail")
        except ValueError:
            pass

        # Wait for half-open
        await asyncio.sleep(0.1)

        # Fail in half-open
        try:
            async with breaker:
                raise ValueError("fail again")
        except ValueError:
            pass

        assert breaker.is_open

    @pytest.mark.asyncio
    async def test_reset(self):
        """Can reset circuit to closed."""
        breaker = CircuitBreaker()
        breaker.force_open()
        assert breaker.is_open

        breaker.reset()
        assert breaker.is_closed

    @pytest.mark.asyncio
    async def test_stats(self):
        """Stats returns circuit information."""
        breaker = CircuitBreaker()

        try:
            async with breaker:
                raise ValueError("fail")
        except ValueError:
            pass

        stats = breaker.stats()
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_protect_decorator(self):
        """protect() decorator works."""
        breaker = CircuitBreaker()

        @breaker.protect
        async def protected_call():
            return "ok"

        result = await protected_call()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_circuit_open_error_retry_after(self):
        """CircuitOpenError includes retry_after hint."""
        config = CircuitBreakerConfig(recovery_timeout=30.0)
        breaker = CircuitBreaker(config)
        breaker.force_open()

        try:
            async with breaker:
                pass
        except CircuitOpenError as e:
            assert e.retry_after is not None
            assert e.retry_after <= 30.0


class TestLoggingRetryCallback:
    """Tests for LoggingRetryCallback."""

    def test_logs_retry(self):
        """Logs retry attempts."""
        logs = []
        callback = LoggingRetryCallback(logger=logs.append)

        callback.on_retry(0, ValueError("test"), 1.5)

        assert len(logs) == 1
        assert "Retry attempt 1" in logs[0]
        assert "1.50s" in logs[0]

    def test_logs_success_after_retry(self):
        """Logs success after retries."""
        logs = []
        callback = LoggingRetryCallback(logger=logs.append)

        callback.on_success(2, "result")

        assert len(logs) == 1
        assert "Succeeded after 3 attempts" in logs[0]

    def test_no_log_on_first_success(self):
        """No log on first-try success."""
        logs = []
        callback = LoggingRetryCallback(logger=logs.append)

        callback.on_success(0, "result")

        assert len(logs) == 0

    def test_logs_failure(self):
        """Logs final failure."""
        logs = []
        callback = LoggingRetryCallback(logger=logs.append)

        callback.on_failure(3, ValueError("error"))

        assert len(logs) == 1
        assert "Failed after 3 attempts" in logs[0]
