from __future__ import annotations

from xsmeteo.models.base import BaseStruct


class FloodResponse(BaseStruct, forbid_unknown_fields=False):
    """Response from the Flood API."""

    latitude: float
    longitude: float
    generationtime_ms: float
