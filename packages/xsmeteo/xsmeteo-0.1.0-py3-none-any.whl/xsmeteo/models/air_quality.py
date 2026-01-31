from __future__ import annotations

from xsmeteo.models.base import BaseStruct


class AirQualityResponse(BaseStruct, forbid_unknown_fields=False):
    """Response from the Air Quality API."""

    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
