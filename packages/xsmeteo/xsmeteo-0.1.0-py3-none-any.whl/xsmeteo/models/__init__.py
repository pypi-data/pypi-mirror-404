from __future__ import annotations

from xsmeteo.models.air_quality import AirQualityResponse
from xsmeteo.models.base import BaseStruct
from xsmeteo.models.climate import ClimateResponse
from xsmeteo.models.common import (
    PrecipitationUnit,
    TemperatureUnit,
    TimeFormat,
    WindSpeedUnit,
)
from xsmeteo.models.elevation import ElevationResponse
from xsmeteo.models.ensemble import EnsembleResponse
from xsmeteo.models.flood import FloodResponse
from xsmeteo.models.forecast import (
    CurrentData,
    DailyData,
    DailyUnits,
    ForecastResponse,
    HourlyData,
    HourlyUnits,
)
from xsmeteo.models.geocoding import GeocodingResponse, GeocodingResult
from xsmeteo.models.historical import HistoricalResponse
from xsmeteo.models.marine import MarineResponse

__all__ = [
    "AirQualityResponse",
    "BaseStruct",
    "ClimateResponse",
    "CurrentData",
    "DailyData",
    "DailyUnits",
    "ElevationResponse",
    "EnsembleResponse",
    "FloodResponse",
    "ForecastResponse",
    "GeocodingResponse",
    "GeocodingResult",
    "HistoricalResponse",
    "HourlyData",
    "HourlyUnits",
    "MarineResponse",
    "PrecipitationUnit",
    "TemperatureUnit",
    "TimeFormat",
    "WindSpeedUnit",
]
