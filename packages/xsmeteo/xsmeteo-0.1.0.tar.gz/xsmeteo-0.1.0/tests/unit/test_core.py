from __future__ import annotations

from xsmeteo.core import config
from xsmeteo.core.rate_limiter import RateLimitConfig


def test_default_rate_limits() -> None:
    limits = config.DEFAULT_RATE_LIMITS

    # Open-Meteo free tier defaults:
    # ~600 per minute
    # 5000 per day
    # 10000 per hour

    assert len(limits) > 0
    assert isinstance(limits[0], RateLimitConfig)

    # Check for the minute limit
    minute_limit = next((lim for lim in limits if lim.period_seconds == 60.0), None)
    assert minute_limit is not None
    assert minute_limit.limit >= 600


def test_host_config() -> None:
    # Ensure hosts are configured correctly
    assert config.ENDPOINTS.FORECAST == "https://api.open-meteo.com/v1/forecast"
    assert config.ENDPOINTS.HISTORICAL == "https://archive-api.open-meteo.com/v1/archive"
    assert config.ENDPOINTS.MARINE == "https://marine-api.open-meteo.com/v1/marine"
