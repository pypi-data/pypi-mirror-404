"""
Forecast service module.

This module contains the logic for interacting with the Open-Meteo Forecast API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.forecast as models
from xsmeteo.services.common import RequestDef


def get_forecast(
    *,
    latitude: float,
    longitude: float,
    hourly: list[str] | None = None,
    daily: list[str] | None = None,
    current: list[str] | None = None,
    temperature_unit: str | None = None,
    wind_speed_unit: str | None = None,
    precipitation_unit: str | None = None,
    timeformat: str | None = None,
    timezone: str | None = None,
    past_days: int | None = None,
    forecast_days: int | None = None,
    models_: list[str] | None = None,  # Renamed from 'models'
) -> RequestDef[models.ForecastResponse]:
    """
    Prepare request for weather forecast data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude (-90 to 90).
    longitude : float
        WGS84 Longitude (-180 to 180).
    hourly : list[str], optional
        List of hourly variables (e.g. ["temperature_2m", "rain"]).
    daily : list[str], optional
        List of daily variables (e.g. ["temperature_2m_max"]).
    current : list[str], optional
        List of current weather variables.
    temperature_unit : str, optional
        "celsius" or "fahrenheit".
    wind_speed_unit : str, optional
        "kmh", "ms", "mph", or "kn".
    precipitation_unit : str, optional
        "mm" or "inch".
    timeformat : str, optional
        "iso8601" or "unixtime".
    timezone : str, optional
        Timezone identifier or "auto".
    past_days : int, optional
        Days of past data to include (0-92).
    forecast_days : int, optional
        Days of forecast to return (1-16).
    models_ : list[str], optional
        Specific weather models to use.

    Returns
    -------
    RequestDef[ForecastResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly,
        "daily": daily,
        "current": current,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "precipitation_unit": precipitation_unit,
        "timeformat": timeformat,
        "timezone": timezone,
        "past_days": past_days,
        "forecast_days": forecast_days,
        "models": models_,
    }
    return RequestDef(
        url=config.ENDPOINTS.FORECAST,
        params=params,
        model=models.ForecastResponse,
    )
