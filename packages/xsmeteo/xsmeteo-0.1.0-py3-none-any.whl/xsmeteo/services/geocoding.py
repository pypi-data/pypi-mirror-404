"""
Geocoding service module.

This module contains the logic for interacting with the Open-Meteo Geocoding API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.geocoding as models
from xsmeteo.services.common import RequestDef


def search_locations(
    *,
    name: str,
    count: int | None = None,
    language: str | None = None,
    format_: str | None = None,
) -> RequestDef[models.GeocodingResponse]:
    """
    Prepare request for location search by name.

    Parameters
    ----------
    name : str
        Name of the city/place (min 2 chars).
    count : int, optional
        Number of results to return.
    language : str, optional
        Language for result names.
    format_ : str, optional
        Response format.

    Returns
    -------
    RequestDef[GeocodingResponse]
        The request definition.
    """
    params = {
        "name": name,
        "count": count,
        "language": language,
        "format": format_,
    }
    return RequestDef(
        url=config.ENDPOINTS.GEOCODING,
        params=params,
        model=models.GeocodingResponse,
    )
