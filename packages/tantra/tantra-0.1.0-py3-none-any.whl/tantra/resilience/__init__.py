"""Resilience components for Tantra.

Provides retry policies, circuit breakers, and rate limiting.

Example:
    from tantra.resilience import RetryPolicy, CircuitBreaker, RateLimiter

    # Retry with exponential backoff
    policy = RetryPolicy(max_retries=5)
    result = await retry_async(api_call, policy=policy)

    # Circuit breaker for failing services
    breaker = CircuitBreaker()
    async with breaker:
        await service.call()

    # Rate limiting
    limiter = RateLimiter(requests_per_minute=100)
    await limiter.acquire()
"""

# Retry and recovery
# Rate limiting
from .ratelimit import (
    ANTHROPIC_TIER1,
    ANTHROPIC_TIER2,
    OPENAI_TIER1,
    OPENAI_TIER2,
    OPENAI_TIER3,
    RateLimitConfig,
    RateLimiter,
    RateLimitError,
)
from .retry import (
    BackoffStrategy,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    LoggingRetryCallback,
    RetryableError,
    RetryCallback,
    RetryPolicy,
    RetryResult,
    retry_async,
    retry_sync,
    with_retry,
)

__all__ = [
    # Retry
    "RetryPolicy",
    "RetryResult",
    "RetryCallback",
    "LoggingRetryCallback",
    "BackoffStrategy",
    "RetryableError",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitOpenError",
    "retry_async",
    "retry_sync",
    "with_retry",
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitError",
    "OPENAI_TIER1",
    "OPENAI_TIER2",
    "OPENAI_TIER3",
    "ANTHROPIC_TIER1",
    "ANTHROPIC_TIER2",
]
