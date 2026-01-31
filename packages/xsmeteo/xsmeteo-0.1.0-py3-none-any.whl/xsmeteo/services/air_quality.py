"""
Air Quality service module.

This module contains the logic for interacting with the Open-Meteo Air Quality API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.air_quality as models
from xsmeteo.services.common import RequestDef


def get_air_quality(
    *,
    latitude: float,
    longitude: float,
    hourly: list[str] | None = None,
    domains: str | None = None,
    timezone: str | None = None,
) -> RequestDef[models.AirQualityResponse]:
    """
    Prepare request for air quality forecast data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude (-90 to 90).
    longitude : float
        WGS84 Longitude (-180 to 180).
    hourly : list[str], optional
        Pollutant variables (e.g. ["pm10", "pm2_5"]).
    domains : str, optional
        "cams_global" or "cams_europe".
    timezone : str, optional
        Timezone setting.

    Returns
    -------
    RequestDef[AirQualityResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly,
        "domains": domains,
        "timezone": timezone,
    }
    return RequestDef(
        url=config.ENDPOINTS.AIR_QUALITY,
        params=params,
        model=models.AirQualityResponse,
    )
