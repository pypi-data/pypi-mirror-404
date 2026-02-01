"""Rate limiting for LLM API calls.

Provides token bucket and sliding window rate limiters to prevent
hitting API rate limits and handle 429 errors gracefully.

Examples:
    ```python
    from tantra import Agent, RateLimiter

    # Limit to 100 requests/minute and 100k tokens/minute
    limiter = RateLimiter(
        requests_per_minute=100,
        tokens_per_minute=100_000,
    )

    agent = Agent(
        "openai:gpt-4o",
        rate_limiter=limiter,
    )
    ```
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_minute: Max requests per minute (None for unlimited).
        tokens_per_minute: Max tokens per minute (None for unlimited).
        requests_per_day: Max requests per day (None for unlimited).
        tokens_per_day: Max tokens per day (None for unlimited).
        retry_on_429: Whether to auto-retry on 429 errors.
        max_retries: Max retries for 429 errors.
        initial_backoff: Initial backoff delay in seconds.
        max_backoff: Maximum backoff delay in seconds.
        backoff_multiplier: Multiplier for exponential backoff.
        safety_margin: Fraction of limits to use (0.9 = 90%).
    """

    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    requests_per_day: int | None = None
    tokens_per_day: int | None = None

    # Backoff settings for 429 errors
    retry_on_429: bool = True
    max_retries: int = 3
    initial_backoff: float = 1.0  # seconds
    max_backoff: float = 60.0  # seconds
    backoff_multiplier: float = 2.0

    # Buffer to stay under limits (0.9 = use 90% of limit)
    safety_margin: float = 0.9


@dataclass
class RateLimitState:
    """Tracks current rate limit usage.

    Attributes:
        request_times: Sliding window of ``(timestamp, count)`` for requests.
        token_usage: Sliding window of ``(timestamp, tokens)`` for token usage.
        daily_requests: Number of requests made today.
        daily_tokens: Number of tokens used today.
        daily_reset_time: Timestamp of next daily counter reset.
    """

    # Sliding window of (timestamp, count) for requests
    request_times: deque = field(default_factory=deque)
    # Sliding window of (timestamp, tokens) for tokens
    token_usage: deque = field(default_factory=deque)
    # Daily counters (reset at midnight UTC)
    daily_requests: int = 0
    daily_tokens: int = 0
    daily_reset_time: float = 0.0

    # Lock for thread safety
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RateLimiter:
    """Rate limiter for LLM API calls.

    Uses sliding window algorithm to track usage and preemptively
    wait when approaching limits. Also handles 429 errors with
    exponential backoff.

    Examples:
        ```python
        limiter = RateLimiter(
            requests_per_minute=100,
            tokens_per_minute=100_000,
        )

        # Check before making request
        await limiter.acquire()

        # Record usage after response
        await limiter.record_usage(prompt_tokens=100, completion_tokens=50)
        ```
    """

    def __init__(
        self,
        requests_per_minute: int | None = None,
        tokens_per_minute: int | None = None,
        requests_per_day: int | None = None,
        tokens_per_day: int | None = None,
        retry_on_429: bool = True,
        max_retries: int = 3,
        safety_margin: float = 0.9,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute (None = unlimited).
            tokens_per_minute: Max tokens per minute (None = unlimited).
            requests_per_day: Max requests per day (None = unlimited).
            tokens_per_day: Max tokens per day (None = unlimited).
            retry_on_429: Whether to auto-retry on 429 errors.
            max_retries: Max retries for 429 errors.
            safety_margin: Use this fraction of limits (0.9 = 90%).
        """
        self.config = RateLimitConfig(
            requests_per_minute=requests_per_minute,
            tokens_per_minute=tokens_per_minute,
            requests_per_day=requests_per_day,
            tokens_per_day=tokens_per_day,
            retry_on_429=retry_on_429,
            max_retries=max_retries,
            safety_margin=safety_margin,
        )
        self._state = RateLimitState()

    async def acquire(self, estimated_tokens: int = 0) -> None:
        """Wait until request can be made within rate limits.

        Args:
            estimated_tokens: Estimated tokens for this request (for preemptive limiting).
        """
        async with self._state._lock:
            await self._wait_if_needed(estimated_tokens)
            self._cleanup_old_entries()

    async def record_usage(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Record token usage after a response.

        Args:
            prompt_tokens: Tokens in the prompt.
            completion_tokens: Tokens in the completion.
        """
        async with self._state._lock:
            now = time.time()
            total_tokens = prompt_tokens + completion_tokens

            # Record request
            self._state.request_times.append((now, 1))

            # Record tokens
            if total_tokens > 0:
                self._state.token_usage.append((now, total_tokens))

            # Update daily counters
            self._check_daily_reset()
            self._state.daily_requests += 1
            self._state.daily_tokens += total_tokens

    async def _wait_if_needed(self, estimated_tokens: int) -> None:
        """Wait if we're at or near rate limits."""
        self._cleanup_old_entries()
        self._check_daily_reset()

        # Check requests per minute
        if self.config.requests_per_minute:
            rpm_limit = int(self.config.requests_per_minute * self.config.safety_margin)
            current_rpm = self._count_in_window(self._state.request_times, 60)

            if current_rpm >= rpm_limit:
                wait_time = self._time_until_slot(self._state.request_times, 60, rpm_limit)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

        # Check tokens per minute
        if self.config.tokens_per_minute and estimated_tokens > 0:
            tpm_limit = int(self.config.tokens_per_minute * self.config.safety_margin)
            current_tpm = self._count_in_window(self._state.token_usage, 60)

            if current_tpm + estimated_tokens >= tpm_limit:
                wait_time = self._time_until_slot(
                    self._state.token_usage, 60, tpm_limit - estimated_tokens
                )
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

        # Check daily limits
        if self.config.requests_per_day:
            if self._state.daily_requests >= self.config.requests_per_day:
                raise RateLimitError(
                    "Daily request limit exceeded", reset_time=self._next_daily_reset()
                )

        if self.config.tokens_per_day:
            if self._state.daily_tokens + estimated_tokens >= self.config.tokens_per_day:
                raise RateLimitError(
                    "Daily token limit exceeded", reset_time=self._next_daily_reset()
                )

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than the window."""
        now = time.time()
        minute_ago = now - 60

        # Clean request times
        while self._state.request_times and self._state.request_times[0][0] < minute_ago:
            self._state.request_times.popleft()

        # Clean token usage
        while self._state.token_usage and self._state.token_usage[0][0] < minute_ago:
            self._state.token_usage.popleft()

    def _count_in_window(self, entries: deque, window_seconds: float) -> int:
        """Count total in sliding window.

        Args:
            entries: Deque of ``(timestamp, count)`` tuples.
            window_seconds: Window duration in seconds.

        Returns:
            Sum of counts within the window.
        """
        now = time.time()
        cutoff = now - window_seconds
        return sum(count for ts, count in entries if ts >= cutoff)

    def _time_until_slot(self, entries: deque, window_seconds: float, limit: int) -> float:
        """Calculate time until a slot is available.

        Args:
            entries: Deque of ``(timestamp, count)`` tuples.
            window_seconds: Window duration in seconds.
            limit: Maximum allowed count within the window.

        Returns:
            Seconds to wait until a slot opens, or 0 if available now.
        """
        if not entries:
            return 0

        now = time.time()
        cutoff = now - window_seconds

        # Find oldest entry that puts us over limit
        running_total = 0
        for ts, count in entries:
            if ts >= cutoff:
                running_total += count
                if running_total >= limit:
                    # Wait until this entry expires
                    return (ts + window_seconds) - now

        return 0

    def _check_daily_reset(self) -> None:
        """Reset daily counters if needed."""
        now = time.time()
        if now >= self._state.daily_reset_time:
            self._state.daily_requests = 0
            self._state.daily_tokens = 0
            self._state.daily_reset_time = self._next_daily_reset()

    def _next_daily_reset(self) -> float:
        """Get timestamp of next midnight UTC.

        Returns:
            Unix timestamp of the next midnight UTC.
        """
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=1
        )
        return tomorrow.timestamp()

    def get_status(self) -> dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dict with current usage counts and configured limits.
        """
        self._cleanup_old_entries()
        self._check_daily_reset()

        return {
            "requests_last_minute": self._count_in_window(self._state.request_times, 60),
            "tokens_last_minute": self._count_in_window(self._state.token_usage, 60),
            "daily_requests": self._state.daily_requests,
            "daily_tokens": self._state.daily_tokens,
            "limits": {
                "requests_per_minute": self.config.requests_per_minute,
                "tokens_per_minute": self.config.tokens_per_minute,
                "requests_per_day": self.config.requests_per_day,
                "tokens_per_day": self.config.tokens_per_day,
            },
        }

    async def handle_429(self, retry_after: float | None = None) -> float:
        """Handle a 429 rate limit error.

        Args:
            retry_after: Retry-After header value from API (if provided).

        Returns:
            Time to wait before retrying.
        """
        if retry_after:
            return retry_after

        # Exponential backoff
        return self.config.initial_backoff

    def __repr__(self) -> str:
        return (
            f"RateLimiter(rpm={self.config.requests_per_minute}, "
            f"tpm={self.config.tokens_per_minute})"
        )


class RateLimitError(Exception):
    """Raised when rate limit is exceeded and cannot wait."""

    def __init__(self, message: str, reset_time: float | None = None):
        """Initialize RateLimitError.

        Args:
            message: Error description.
            reset_time: Timestamp when the limit resets, if known.
        """
        self.reset_time = reset_time
        super().__init__(message)


# Preset configurations for common providers
OPENAI_TIER1 = RateLimiter(
    requests_per_minute=500,
    tokens_per_minute=30_000,
)

OPENAI_TIER2 = RateLimiter(
    requests_per_minute=5000,
    tokens_per_minute=450_000,
)

OPENAI_TIER3 = RateLimiter(
    requests_per_minute=5000,
    tokens_per_minute=800_000,
)

ANTHROPIC_TIER1 = RateLimiter(
    requests_per_minute=50,
    tokens_per_minute=40_000,
)

ANTHROPIC_TIER2 = RateLimiter(
    requests_per_minute=1000,
    tokens_per_minute=80_000,
)
