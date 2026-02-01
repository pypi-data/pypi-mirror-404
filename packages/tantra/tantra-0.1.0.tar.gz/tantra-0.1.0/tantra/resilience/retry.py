"""Retry and Recovery for Tantra.

Provides automatic retry with exponential backoff for transient failures,
configurable retry policies, and circuit breaker pattern.
"""

from __future__ import annotations

import asyncio
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from ..exceptions import ProviderError


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""

    pass


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and requests are rejected."""

    def __init__(self, message: str = "Circuit breaker is open", retry_after: float | None = None):
        """Initialize CircuitOpenError.

        Args:
            message: Error description.
            retry_after: Seconds until the circuit may transition to half-open.
        """
        super().__init__(message)
        self.retry_after = retry_after


class BackoffStrategy(str, Enum):
    """Backoff strategies for retry delays."""

    CONSTANT = "constant"  # Same delay each time
    LINEAR = "linear"  # Delay increases linearly
    EXPONENTIAL = "exponential"  # Delay doubles each time
    EXPONENTIAL_JITTER = "exponential_jitter"  # Exponential with random jitter


@dataclass
class RetryPolicy:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts.
        backoff: Backoff strategy to use.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter_factor: Random jitter factor (0.0 to 1.0).
        retryable_exceptions: Exception types that trigger retries.
        retryable_status_codes: HTTP status codes that trigger retries.

    Examples:
        ```python
        # Default policy: 3 retries with exponential backoff
        policy = RetryPolicy()

        # Custom policy: 5 retries with constant 1s delay
        policy = RetryPolicy(
            max_retries=5,
            backoff=BackoffStrategy.CONSTANT,
            base_delay=1.0,
        )

        # Aggressive retry: many retries with jitter
        policy = RetryPolicy(
            max_retries=10,
            backoff=BackoffStrategy.EXPONENTIAL_JITTER,
            base_delay=0.5,
            max_delay=30.0,
        )
        ```
    """

    max_retries: int = 3
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    jitter_factor: float = 0.5  # 0-1, how much randomness to add
    retryable_exceptions: tuple[type[Exception], ...] = (
        ProviderError,
        RetryableError,
        ConnectionError,
        TimeoutError,
    )
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number (0-indexed).

        Args:
            attempt: Zero-indexed attempt number.

        Returns:
            Delay in seconds, capped at ``max_delay``.
        """
        if self.backoff == BackoffStrategy.CONSTANT:
            delay = self.base_delay
        elif self.backoff == BackoffStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        elif self.backoff == BackoffStrategy.EXPONENTIAL:
            delay = self.base_delay * (2**attempt)
        elif self.backoff == BackoffStrategy.EXPONENTIAL_JITTER:
            delay = self.base_delay * (2**attempt)
            jitter = delay * self.jitter_factor * random.random()
            delay = delay + jitter
        else:
            delay = self.base_delay

        return min(delay, self.max_delay)

    def is_retryable(self, error: Exception) -> bool:
        """Check if an error should trigger a retry.

        Args:
            error: The exception to evaluate.

        Returns:
            True if the error matches retryable criteria.
        """
        # Check exception type
        if isinstance(error, self.retryable_exceptions):
            return True

        # Check for HTTP status codes in ProviderError
        if isinstance(error, ProviderError):
            # Check if error has a status_code attribute
            status_code = getattr(error, "status_code", None)
            if status_code and status_code in self.retryable_status_codes:
                return True

        return False


@dataclass
class RetryResult:
    """Result of a retry operation.

    Attributes:
        success: Whether the operation eventually succeeded.
        result: The return value on success.
        error: The last exception on failure.
        attempts: Total number of attempts made.
        total_delay: Cumulative delay in seconds across retries.
        delays: Individual delay times for each retry.
    """

    success: bool
    result: Any = None
    error: Exception | None = None
    attempts: int = 0
    total_delay: float = 0.0
    delays: list[float] = field(default_factory=list)


class RetryCallback(ABC):
    """Callback interface for retry events."""

    @abstractmethod
    def on_retry(
        self,
        attempt: int,
        error: Exception,
        delay: float,
    ) -> None:
        """Called before each retry attempt.

        Args:
            attempt: Zero-indexed attempt number.
            error: The exception that triggered the retry.
            delay: Seconds to wait before retrying.
        """
        pass

    @abstractmethod
    def on_success(self, attempt: int, result: Any) -> None:
        """Called when operation succeeds.

        Args:
            attempt: Zero-indexed attempt number that succeeded.
            result: The successful return value.
        """
        pass

    @abstractmethod
    def on_failure(self, attempts: int, error: Exception) -> None:
        """Called when all retries are exhausted.

        Args:
            attempts: Total number of attempts made.
            error: The last exception encountered.
        """
        pass


class LoggingRetryCallback(RetryCallback):
    """Retry callback that logs events."""

    def __init__(self, logger: Callable[[str], None] | None = None):
        """Initialize logging callback.

        Args:
            logger: Callable that accepts a log message string. Defaults to ``print``.
        """
        self.logger = logger or print

    def on_retry(self, attempt: int, error: Exception, delay: float) -> None:
        self.logger(f"Retry attempt {attempt + 1} after {delay:.2f}s: {error}")

    def on_success(self, attempt: int, result: Any) -> None:
        if attempt > 0:
            self.logger(f"Succeeded after {attempt + 1} attempts")

    def on_failure(self, attempts: int, error: Exception) -> None:
        self.logger(f"Failed after {attempts} attempts: {error}")


T = TypeVar("T")


async def retry_async(
    func: Callable[..., T],
    *args: Any,
    policy: RetryPolicy | None = None,
    callback: RetryCallback | None = None,
    **kwargs: Any,
) -> T:
    """Execute an async function with retry logic.

    Args:
        func: The async function to execute.
        *args: Positional arguments for the function.
        policy: Retry policy configuration.
        callback: Optional callback for retry events.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function.

    Raises:
        Exception: The last exception if all retries fail.

    Examples:
        ```python
        result = await retry_async(
            provider.complete,
            messages,
            policy=RetryPolicy(max_retries=5),
        )
        ```
    """
    policy = policy or RetryPolicy()
    last_error: Exception | None = None
    total_delay = 0.0
    delays: list[float] = []

    for attempt in range(policy.max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if callback:
                callback.on_success(attempt, result)
            return result

        except Exception as e:
            last_error = e

            # Check if we should retry
            if attempt >= policy.max_retries or not policy.is_retryable(e):
                if callback:
                    callback.on_failure(attempt + 1, e)
                raise

            # Calculate and apply delay
            delay = policy.calculate_delay(attempt)
            delays.append(delay)
            total_delay += delay

            if callback:
                callback.on_retry(attempt, e, delay)

            await asyncio.sleep(delay)

    # Should not reach here, but just in case
    if last_error:
        raise last_error
    raise RuntimeError("Retry loop exited unexpectedly")


def retry_sync(
    func: Callable[..., T],
    *args: Any,
    policy: RetryPolicy | None = None,
    callback: RetryCallback | None = None,
    **kwargs: Any,
) -> T:
    """Execute a sync function with retry logic.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        policy: Retry policy configuration.
        callback: Optional callback for retry events.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function.

    Raises:
        Exception: The last exception if all retries fail.
    """
    policy = policy or RetryPolicy()
    last_error: Exception | None = None

    for attempt in range(policy.max_retries + 1):
        try:
            result = func(*args, **kwargs)
            if callback:
                callback.on_success(attempt, result)
            return result

        except Exception as e:
            last_error = e

            if attempt >= policy.max_retries or not policy.is_retryable(e):
                if callback:
                    callback.on_failure(attempt + 1, e)
                raise

            delay = policy.calculate_delay(attempt)

            if callback:
                callback.on_retry(attempt, e, delay)

            time.sleep(delay)

    if last_error:
        raise last_error
    raise RuntimeError("Retry loop exited unexpectedly")


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================


class CircuitState(str, Enum):
    """States for circuit breaker."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker.

    Attributes:
        failure_threshold: Number of failures before opening the circuit.
        recovery_timeout: Seconds to wait before transitioning to half-open.
        success_threshold: Successes needed in half-open to close the circuit.
        half_open_max_calls: Maximum concurrent calls allowed in half-open state.

    Examples:
        ```python
        config = CircuitBreakerConfig(
            failure_threshold=5,  # Open after 5 failures
            recovery_timeout=30.0,  # Wait 30s before testing
            success_threshold=2,  # Need 2 successes to close
        )
        ```
    """

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 30.0  # Seconds to wait before half-open
    success_threshold: int = 2  # Successes needed to close from half-open
    half_open_max_calls: int = 3  # Max concurrent calls in half-open


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered

    Examples:
        ```python
        breaker = CircuitBreaker()

        async def call_service():
            async with breaker:
                return await service.call()

        # Or use the decorator
        @breaker.protect
        async def call_service():
            return await service.call()
        ```
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration. Uses defaults if None.
        """
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Whether circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Whether circuit is open (rejecting requests)."""
        return self._state == CircuitState.OPEN

    @property
    def failure_count(self) -> int:
        """Current failure count."""
        return self._failure_count

    async def _check_state(self) -> None:
        """Check and potentially update circuit state."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time is not None:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.config.recovery_timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        self._success_count = 0

    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def _record_failure(self) -> None:
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN

    async def __aenter__(self) -> CircuitBreaker:
        """Enter the circuit breaker context."""
        await self._check_state()

        if self._state == CircuitState.OPEN:
            retry_after = None
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                retry_after = max(0, self.config.recovery_timeout - elapsed)
            raise CircuitOpenError(retry_after=retry_after)

        if self._state == CircuitState.HALF_OPEN:
            async with self._lock:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitOpenError("Too many half-open calls")
                self._half_open_calls += 1

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the circuit breaker context."""
        if exc_type is None:
            await self._record_success()
        else:
            await self._record_failure()

    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect a function with this circuit breaker.

        Args:
            func: The async function to protect.

        Returns:
            Wrapped function that checks circuit state before execution.
        """

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async with self:
                return await func(*args, **kwargs)

        return wrapper

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0

    def force_open(self) -> None:
        """Force the circuit to open state."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()

    def stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dict with state, failure_count, success_count, and last_failure_time.
        """
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
        }


# =============================================================================
# Retry Decorator
# =============================================================================


def with_retry(
    policy: RetryPolicy | None = None,
    callback: RetryCallback | None = None,
) -> Callable:
    """Decorator to add retry logic to a function.

    Examples:
        ```python
        @with_retry(RetryPolicy(max_retries=5))
        async def call_api():
            return await api.request()

        # With callback
        @with_retry(policy=policy, callback=LoggingRetryCallback())
        async def call_api():
            return await api.request()
        ```
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                return await retry_async(func, *args, policy=policy, callback=callback, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                return retry_sync(func, *args, policy=policy, callback=callback, **kwargs)

            return sync_wrapper

    return decorator
