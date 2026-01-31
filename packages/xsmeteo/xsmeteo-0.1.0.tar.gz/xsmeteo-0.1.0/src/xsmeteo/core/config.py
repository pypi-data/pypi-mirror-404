from __future__ import annotations

import msgspec

from xsmeteo.core.rate_limiter import RateLimitConfig


class APIEndpoints(msgspec.Struct, frozen=True):
    """Base URLs for all Open-Meteo API endpoints."""

    FORECAST: str = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL: str = "https://archive-api.open-meteo.com/v1/archive"
    MARINE: str = "https://marine-api.open-meteo.com/v1/marine"
    AIR_QUALITY: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    GEOCODING: str = "https://geocoding-api.open-meteo.com/v1/search"
    ELEVATION: str = "https://api.open-meteo.com/v1/elevation"
    FLOOD: str = "https://flood-api.open-meteo.com/v1/flood"
    ENSEMBLE: str = "https://ensemble-api.open-meteo.com/v1/ensemble"
    CLIMATE: str = "https://climate-api.open-meteo.com/v1/climate"


# Default API endpoints instance
ENDPOINTS = APIEndpoints()


# Default rate limits based on Open-Meteo fair use policy
DEFAULT_RATE_LIMITS: list[RateLimitConfig] = [
    RateLimitConfig(limit=600, period_seconds=60.0),  # Minutely
    RateLimitConfig(limit=5000, period_seconds=3600.0),  # Hourly
    RateLimitConfig(limit=10000, period_seconds=86400.0),  # Daily
]
