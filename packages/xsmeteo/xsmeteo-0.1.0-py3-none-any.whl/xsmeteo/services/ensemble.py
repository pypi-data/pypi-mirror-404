"""
Ensemble service module.

This module contains the logic for interacting with the Open-Meteo Ensemble API.
"""

from __future__ import annotations

import xsmeteo.core.config as config
import xsmeteo.models.ensemble as models
from xsmeteo.services.common import RequestDef


def get_ensemble(
    *,
    latitude: float,
    longitude: float,
    models_: list[str],
    hourly: list[str] | None = None,
) -> RequestDef[models.EnsembleResponse]:
    """
    Prepare request for ensemble forecast data.

    Parameters
    ----------
    latitude : float
        WGS84 Latitude.
    longitude : float
        WGS84 Longitude.
    models_ : list[str]
        Target ensemble model(s) (e.g. ["icon_seamless"]).
    hourly : list[str], optional
        Variables to retrieve.

    Returns
    -------
    RequestDef[EnsembleResponse]
        The request definition.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "models": models_,
        "hourly": hourly,
    }
    return RequestDef(
        url=config.ENDPOINTS.ENSEMBLE,
        params=params,
        model=models.EnsembleResponse,
    )
