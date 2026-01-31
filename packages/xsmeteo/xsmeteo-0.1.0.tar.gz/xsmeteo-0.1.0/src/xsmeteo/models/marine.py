from __future__ import annotations

from xsmeteo.models.base import BaseStruct


class MarineResponse(BaseStruct, forbid_unknown_fields=False):
    """Response from the Marine Weather API."""

    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
