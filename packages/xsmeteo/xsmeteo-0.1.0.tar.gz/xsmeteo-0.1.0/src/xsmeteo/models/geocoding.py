from __future__ import annotations

from xsmeteo.models.base import BaseStruct


class GeocodingResult(BaseStruct, forbid_unknown_fields=False):
    """A single geocoding result."""

    id: int
    name: str
    latitude: float
    longitude: float
    elevation: float | None = None
    feature_code: str | None = None
    country_code: str | None = None
    admin1_id: int | None = None
    admin2_id: int | None = None
    admin3_id: int | None = None
    admin4_id: int | None = None
    timezone: str | None = None
    population: int | None = None
    postcodes: list[str] | None = None
    country_id: int | None = None
    country: str | None = None
    admin1: str | None = None
    admin2: str | None = None
    admin3: str | None = None
    admin4: str | None = None


class GeocodingResponse(BaseStruct):
    """Response from the Geocoding API."""

    results: list[GeocodingResult] | None = None
    generationtime_ms: float | None = None
