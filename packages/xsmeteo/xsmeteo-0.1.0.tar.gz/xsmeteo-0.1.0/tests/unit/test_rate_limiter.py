from __future__ import annotations

import time

import pytest

from xsmeteo.core.rate_limiter import RateLimitConfig, RateLimiter


def test_rate_limiter_sync_basic() -> None:
    config = RateLimitConfig(limit=5, period_seconds=1.0)
    limiter = RateLimiter([config])

    start = time.monotonic()
    for _ in range(5):
        limiter.acquire_sync()
    duration = time.monotonic() - start
    assert duration < 0.1  # Should be instant


def test_rate_limiter_sync_blocking() -> None:
    config = RateLimitConfig(limit=1, period_seconds=0.1)
    limiter = RateLimiter([config])

    limiter.acquire_sync()  # First one free
    start = time.monotonic()
    limiter.acquire_sync()  # Should block
    duration = time.monotonic() - start
    assert duration >= 0.09  # Approx 0.1s


@pytest.mark.asyncio
async def test_rate_limiter_async_basic() -> None:
    config = RateLimitConfig(limit=5, period_seconds=1.0)
    limiter = RateLimiter([config])

    start = time.monotonic()
    for _ in range(5):
        await limiter.acquire_async()
    duration = time.monotonic() - start
    assert duration < 0.1


@pytest.mark.asyncio
async def test_rate_limiter_async_wait() -> None:
    config = RateLimitConfig(limit=1, period_seconds=0.1)
    limiter = RateLimiter([config])

    await limiter.acquire_async()
    start = time.monotonic()
    await limiter.acquire_async()
    duration = time.monotonic() - start
    assert duration >= 0.09
