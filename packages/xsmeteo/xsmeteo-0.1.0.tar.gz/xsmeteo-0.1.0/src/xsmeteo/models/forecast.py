from __future__ import annotations

import typing

from xsmeteo.models.base import BaseStruct


class HourlyUnits(BaseStruct, forbid_unknown_fields=False):
    """Units for hourly variables."""

    time: str = "iso8601"


class DailyUnits(BaseStruct, forbid_unknown_fields=False):
    """Units for daily variables."""

    time: str = "iso8601"


class HourlyData(BaseStruct, forbid_unknown_fields=False):
    """Hourly weather data."""

    time: list[str]


class DailyData(BaseStruct, forbid_unknown_fields=False):
    """Daily weather data."""

    time: list[str]


class CurrentData(BaseStruct, forbid_unknown_fields=False):
    """Current weather data."""

    time: str
    interval: int


class ForecastResponse(BaseStruct, forbid_unknown_fields=False):
    """Response from the Forecast API."""

    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    hourly_units: HourlyUnits | None = None
    hourly: HourlyData | None = None
    daily_units: DailyUnits | None = None
    daily: DailyData | None = None
    current_units: typing.Any | None = None
    current: CurrentData | None = None
