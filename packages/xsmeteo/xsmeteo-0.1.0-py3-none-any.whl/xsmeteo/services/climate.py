"""
Climate service module.

This module contains the logic for interacting with the Open-Meteo Climate API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.climate as models
from xsmeteo.services.common import RequestDef


def get_climate(
    *,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    models_: list[str] | None = None,
    daily: list[str] | None = None,
) -> RequestDef[models.ClimateResponse]:
    """
    Prepare request for climate projection data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude.
    longitude : float
        WGS84 Longitude.
    start_date : str
        Start date (e.g. "1950-01-01").
    end_date : str
        End date (e.g. "2050-12-31").
    models_ : list[str], optional
        CMIP6 models (e.g. ["EC_Earth3P_HR"]).
    daily : list[str], optional
        Daily climate variables.

    Returns
    -------
    RequestDef[ClimateResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "models": models_,
        "daily": daily,
    }
    return RequestDef(
        url=config.ENDPOINTS.CLIMATE,
        params=params,
        model=models.ClimateResponse,
    )
