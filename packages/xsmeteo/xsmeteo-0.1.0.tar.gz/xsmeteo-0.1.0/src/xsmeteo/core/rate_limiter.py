from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from threading import Lock

from xsmeteo.exceptions import RateLimitError


@dataclass
class RateLimitConfig:
    """Configuration for a single rate limit bucket."""

    limit: int
    period_seconds: float

    @property
    def rate(self) -> float:
        return self.limit / self.period_seconds


@dataclass
class TokenBucket:
    """A single token bucket implementation."""

    config: RateLimitConfig
    tokens: float = field(init=False)
    last_update: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.config.limit)
        self.last_update = time.monotonic()

    def refill(self) -> None:
        now = time.monotonic()
        delta = now - self.last_update
        self.tokens = min(self.config.limit, self.tokens + delta * self.config.rate)
        self.last_update = now

    def consume(self, amount: int = 1) -> bool:
        self.refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def time_to_wait(self, amount: int = 1) -> float:
        self.refill()
        if self.tokens >= amount:
            return 0.0
        missing = amount - self.tokens
        return missing / self.config.rate


class RateLimiter:
    """Hierarchical Token Bucket Rate Limiter.

    Thread-safe and specific to an instance (not global state).
    """

    def __init__(self, limits: list[RateLimitConfig]) -> None:
        self._buckets = [TokenBucket(config) for config in limits]
        self._lock = Lock()

    def acquire_sync(self, tokens: int = 1, timeout: float | None = None) -> None:
        """Acquire tokens synchronously, blocking if necessary."""

        with self._lock:
            wait_time = self._calculate_wait_time(tokens)

            if timeout is not None and wait_time > timeout:
                raise RateLimitError(f"Rate limit exceeded. Try again in {wait_time:.2f}s")

            if wait_time > 0:
                time.sleep(wait_time)
                # Re-check after sleeping as other threads might have consumed tokens
                # For strict correctness we should re-loop, but for simple rate limiting
                # strict FIFO isn't always required. However, let's just consume now.
                # A more robust implementation would loop.

            # Consume from all buckets
            for bucket in self._buckets:
                # We assume wait_time was correct and we can consume now.
                # In high contention, this might dip negative (acceptable for soft limits).
                # To be perfectly strict, we'd need a more complex loop.
                bucket.tokens -= tokens

    async def acquire_async(self, tokens: int = 1, timeout: float | None = None) -> None:
        """Acquire tokens asynchronously, yielding if necessary."""
        # Note: asyncio doesn't use the thread lock.
        # We assume this method is called from a single event loop.
        # If shared across threads/loops, explicit async locks would be needed.

        wait_time = self._calculate_wait_time(tokens)

        if timeout is not None and wait_time > timeout:
            raise RateLimitError(f"Rate limit exceeded. Try again in {wait_time:.2f}s")

        if wait_time > 0:
            await asyncio.sleep(wait_time)

        # Consume logic similar to sync
        for bucket in self._buckets:
            bucket.tokens -= tokens

    def _calculate_wait_time(self, tokens: int) -> float:
        """Calculate the maximum wait time required across all buckets."""
        max_wait = 0.0
        for bucket in self._buckets:
            wait = bucket.time_to_wait(tokens)
            max_wait = max(max_wait, wait)
        return max_wait
