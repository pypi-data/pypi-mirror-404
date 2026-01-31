"""
Flood service module.

This module contains the logic for interacting with the Open-Meteo Flood API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.flood as models
from xsmeteo.services.common import RequestDef


def get_flood(
    *,
    latitude: float,
    longitude: float,
    daily: list[str] | None = None,
    ensemble: bool | None = None,
) -> RequestDef[models.FloodResponse]:
    """
    Prepare request for flood/river discharge forecast data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude.
    longitude : float
        WGS84 Longitude.
    daily : list[str], optional
        Flood variables (e.g. ["river_discharge"]).
    ensemble : bool, optional
        If true, returns all 51 ensemble members.

    Returns
    -------
    RequestDef[FloodResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": daily,
        "ensemble": ensemble,
    }
    return RequestDef(
        url=config.ENDPOINTS.FLOOD,
        params=params,
        model=models.FloodResponse,
    )
