"""
Marine service module.

This module contains the logic for interacting with the Open-Meteo Marine API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.marine as models
from xsmeteo.services.common import RequestDef


def get_marine(
    *,
    latitude: float,
    longitude: float,
    hourly: list[str] | None = None,
    daily: list[str] | None = None,
    timezone: str | None = None,
    cell_selection: str | None = None,
) -> RequestDef[models.MarineResponse]:
    """
    Prepare request for marine/ocean weather data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude (-90 to 90).
    longitude : float
        WGS84 Longitude (-180 to 180).
    hourly : list[str], optional
        Marine hourly variables (e.g. ["wave_height"]).
    daily : list[str], optional
        Marine daily variables.
    timezone : str, optional
        Timezone setting.
    cell_selection : str, optional
        "sea", "land", or "nearest".

    Returns
    -------
    RequestDef[MarineResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly,
        "daily": daily,
        "timezone": timezone,
        "cell_selection": cell_selection,
    }
    return RequestDef(
        url=config.ENDPOINTS.MARINE,
        params=params,
        model=models.MarineResponse,
    )
