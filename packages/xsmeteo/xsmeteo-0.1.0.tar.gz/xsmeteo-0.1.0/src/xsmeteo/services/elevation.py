"""
Elevation service module.

This module contains the logic for interacting with the Open-Meteo Elevation API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.elevation as models
from xsmeteo.services.common import RequestDef


def get_elevation(
    *,
    latitude: float | list[float],
    longitude: float | list[float],
) -> RequestDef[models.ElevationResponse]:
    """
    Prepare request for elevation data.

    Parameters
    ----------
    latitude : float | list[float]
        Single or list of latitudes.
    longitude : float | list[float]
        Single or list of longitudes.

    Returns
    -------
    RequestDef[ElevationResponse]
        The request definition.
    """
    lat_str = (
        ",".join(str(lat) for lat in latitude) if isinstance(latitude, list) else str(latitude)
    )
    lon_str = (
        ",".join(str(lon) for lon in longitude) if isinstance(longitude, list) else str(longitude)
    )
    params = {"latitude": lat_str, "longitude": lon_str}
    return RequestDef(
        url=config.ENDPOINTS.ELEVATION,
        params=params,
        model=models.ElevationResponse,
    )
