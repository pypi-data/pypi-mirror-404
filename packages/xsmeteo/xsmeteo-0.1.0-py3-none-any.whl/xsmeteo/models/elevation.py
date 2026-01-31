from __future__ import annotations

from xsmeteo.models.base import BaseStruct


class ElevationResponse(BaseStruct):
    """Response from the Elevation API."""

    elevation: list[float]
