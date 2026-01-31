"""
Historical service module.

This module contains the logic for interacting with the Open-Meteo Historical API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.historical as models
from xsmeteo.services.common import RequestDef


def get_historical(
    *,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    hourly: list[str] | None = None,
    daily: list[str] | None = None,
    models_: str | None = None,
    timezone: str | None = None,
) -> RequestDef[models.HistoricalResponse]:
    """
    Prepare request for historical weather data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude (-90 to 90).
    longitude : float
        WGS84 Longitude (-180 to 180).
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).
    hourly : list[str], optional
        Historical hourly variables.
    daily : list[str], optional
        Historical daily variables.
    models_ : str, optional
        Reanalysis model selector.
    timezone : str, optional
        Timezone for time alignment.

    Returns
    -------
    RequestDef[HistoricalResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": hourly,
        "daily": daily,
        "models": models_,
        "timezone": timezone,
    }
    return RequestDef(
        url=config.ENDPOINTS.HISTORICAL,
        params=params,
        model=models.HistoricalResponse,
    )
