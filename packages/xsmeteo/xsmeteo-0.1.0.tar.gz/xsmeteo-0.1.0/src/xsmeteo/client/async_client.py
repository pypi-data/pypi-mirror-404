"""
Asynchronous client for Open-Meteo API.
"""

from __future__ import annotations

import typing

import httpx
import msgspec

import xsmeteo.core.config as config
import xsmeteo.core.rate_limiter as rate_limiter
import xsmeteo.exceptions as exceptions
import xsmeteo.models.air_quality as air_quality_models
import xsmeteo.models.climate as climate_models
import xsmeteo.models.elevation as elevation_models
import xsmeteo.models.ensemble as ensemble_models
import xsmeteo.models.flood as flood_models
import xsmeteo.models.forecast as forecast_models
import xsmeteo.models.geocoding as geocoding_models
import xsmeteo.models.historical as historical_models
import xsmeteo.models.marine as marine_models
import xsmeteo.services.air_quality as air_quality_service
import xsmeteo.services.climate as climate_service
import xsmeteo.services.elevation as elevation_service
import xsmeteo.services.ensemble as ensemble_service
import xsmeteo.services.flood as flood_service
import xsmeteo.services.forecast as forecast_service
import xsmeteo.services.geocoding as geocoding_service
import xsmeteo.services.historical as historical_service
import xsmeteo.services.marine as marine_service

if typing.TYPE_CHECKING:
    from typing import TypeVar

    from xsmeteo.services.common import RequestDef

    T = TypeVar("T")


class AsyncXSMeteo:
    """
    Asynchronous client for Open-Meteo API.

    Examples
    --------
    >>> async with AsyncXSMeteo() as client:
    ...     forecast = await client.get_forecast(latitude=52.52, longitude=13.41)
    """

    def __init__(
        self,
        *,
        rate_limits: list[rate_limiter.RateLimitConfig] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        rate_limits : list[RateLimitConfig], optional
            Custom rate limits.
        timeout : float, optional
            Timeout for requests in seconds. Default is 30.0.
        """
        self._rate_limiter = rate_limiter.RateLimiter(rate_limits or config.DEFAULT_RATE_LIMITS)
        self._client = httpx.AsyncClient(timeout=timeout)
        self._decoder = msgspec.json.Decoder()

    async def __aenter__(self) -> AsyncXSMeteo:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: typing.Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(self, request_def: RequestDef[T]) -> T:
        """
        Make an async HTTP GET request with rate limiting.

        Parameters
        ----------
        request_def : RequestDef[T]
            The request definition.

        Returns
        -------
        T
            The response decoded into the specified model.

        Raises
        ------
        HTTPError
            If the API returns an error status.
        DecodeError
            If response decoding fails.
        """
        await self._rate_limiter.acquire_async()

        response = await self._client.get(
            request_def.url,
            params=self._serialize_params(request_def.params),
        )

        if response.status_code != 200:
            self._handle_error(response)

        try:
            return msgspec.json.decode(response.content, type=request_def.model)
        except msgspec.DecodeError as e:
            raise exceptions.DecodeError(str(e)) from e

    def _handle_error(self, response: httpx.Response) -> typing.NoReturn:
        """
        Handle HTTP error responses.

        Parameters
        ----------
        response : httpx.Response
            The HTTP response object.

        Raises
        ------
        HTTPError
            The parsed error from the response.
        """
        try:
            error_data: dict[str, typing.Any] = self._decoder.decode(response.content)
            reason = error_data.get("reason", "Unknown error")
        except msgspec.DecodeError:
            reason = response.text or "Unknown error"
        raise exceptions.HTTPError(reason, response.status_code)

    @staticmethod
    def _serialize_params(params: dict[str, typing.Any]) -> dict[str, str]:
        """
        Serialize parameters to string format for URL encoding.

        Parameters
        ----------
        params : dict[str, Any]
            The parameters to serialize.

        Returns
        -------
        dict[str, str]
            The serialized parameters.
        """
        result: dict[str, str] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, list):
                result[key] = ",".join(str(v) for v in value)
            elif isinstance(value, bool):
                result[key] = str(value).lower()
            else:
                result[key] = str(value)
        return result

    # Forecast API

    async def get_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        hourly: list[str] | None = None,
        daily: list[str] | None = None,
        current: list[str] | None = None,
        temperature_unit: str | None = None,
        wind_speed_unit: str | None = None,
        precipitation_unit: str | None = None,
        timeformat: str | None = None,
        timezone: str | None = None,
        past_days: int | None = None,
        forecast_days: int | None = None,
        models: list[str] | None = None,
    ) -> forecast_models.ForecastResponse:
        """
        Get weather forecast data.

        Parameters
        ----------
        latitude : float
            WGS84 Latitude (-90 to 90).
        longitude : float
            WGS84 Longitude (-180 to 180).
        hourly : list[str], optional
            List of hourly variables (e.g. ["temperature_2m", "rain"]).
        daily : list[str], optional
            List of daily variables (e.g. ["temperature_2m_max"]).
        current : list[str], optional
            List of current weather variables.
        temperature_unit : str, optional
            "celsius" or "fahrenheit".
        wind_speed_unit : str, optional
            "kmh", "ms", "mph", or "kn".
        precipitation_unit : str, optional
            "mm" or "inch".
        timeformat : str, optional
            "iso8601" or "unixtime".
        timezone : str, optional
            Timezone identifier or "auto".
        past_days : int, optional
            Days of past data to include (0-92).
        forecast_days : int, optional
            Days of forecast to return (1-16).
        models : list[str], optional
            Specific weather models.

        Returns
        -------
        ForecastResponse
            The parsed weather forecast data.
        """
        req_def = forecast_service.get_forecast(
            latitude=latitude,
            longitude=longitude,
            hourly=hourly,
            daily=daily,
            current=current,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
            precipitation_unit=precipitation_unit,
            timeformat=timeformat,
            timezone=timezone,
            past_days=past_days,
            forecast_days=forecast_days,
            models_=models,
        )
        return await self._request(req_def)

    # Historical API

    async def get_historical(
        self,
        *,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        hourly: list[str] | None = None,
        daily: list[str] | None = None,
        models: str | None = None,
        timezone: str | None = None,
    ) -> historical_models.HistoricalResponse:
        """
        Get historical weather data.

        Parameters
        ----------
        latitude : float
            WGS84 Latitude.
        longitude : float
            WGS84 Longitude.
        start_date : str
            Start date (YYYY-MM-DD).
        end_date : str
            End date (YYYY-MM-DD).
        hourly : list[str], optional
            Historical hourly variables.
        daily : list[str], optional
            Historical daily variables.
        models : str, optional
            Reanalysis model selector.
        timezone : str, optional
            Timezone for time alignment.

        Returns
        -------
        HistoricalResponse
            The parsed historical weather data.
        """
        req_def = historical_service.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            hourly=hourly,
            daily=daily,
            models_=models,
            timezone=timezone,
        )
        return await self._request(req_def)

    # Marine API

    async def get_marine(
        self,
        *,
        latitude: float,
        longitude: float,
        hourly: list[str] | None = None,
        daily: list[str] | None = None,
        timezone: str | None = None,
        cell_selection: str | None = None,
    ) -> marine_models.MarineResponse:
        """
        Get marine/ocean weather data.

        Parameters
        ----------
        latitude : float
            WGS84 Latitude.
        longitude : float
            WGS84 Longitude.
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
        MarineResponse
            The parsed marine weather data.
        """
        req_def = marine_service.get_marine(
            latitude=latitude,
            longitude=longitude,
            hourly=hourly,
            daily=daily,
            timezone=timezone,
            cell_selection=cell_selection,
        )
        return await self._request(req_def)

    # Air Quality API

    async def get_air_quality(
        self,
        *,
        latitude: float,
        longitude: float,
        hourly: list[str] | None = None,
        domains: str | None = None,
        timezone: str | None = None,
    ) -> air_quality_models.AirQualityResponse:
        """
        Get air quality forecast data.

        Parameters
        ----------
        latitude : float
            WGS84 Latitude.
        longitude : float
            WGS84 Longitude.
        hourly : list[str], optional
            Pollutant variables (e.g. ["pm10", "pm2_5"]).
        domains : str, optional
            "cams_global" or "cams_europe".
        timezone : str, optional
            Timezone setting.

        Returns
        -------
        AirQualityResponse
            The parsed air quality data.
        """
        req_def = air_quality_service.get_air_quality(
            latitude=latitude,
            longitude=longitude,
            hourly=hourly,
            domains=domains,
            timezone=timezone,
        )
        return await self._request(req_def)

    # Geocoding API

    async def search_locations(
        self,
        *,
        name: str,
        count: int | None = None,
        language: str | None = None,
        format_: str | None = None,
    ) -> geocoding_models.GeocodingResponse:
        """
        Search for locations by name (forward geocoding).

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
        GeocodingResponse
            JSON response with location results.
        """
        req_def = geocoding_service.search_locations(
            name=name,
            count=count,
            language=language,
            format_=format_,
        )
        return await self._request(req_def)

    # Elevation API

    async def get_elevation(
        self,
        *,
        latitude: float | list[float],
        longitude: float | list[float],
    ) -> elevation_models.ElevationResponse:
        """
        Get elevation data for coordinates.

        Parameters
        ----------
        latitude : float | list[float]
            Single or list of latitudes.
        longitude : float | list[float]
            Single or list of longitudes.

        Returns
        -------
        ElevationResponse
            JSON response with elevation data.
        """
        req_def = elevation_service.get_elevation(
            latitude=latitude,
            longitude=longitude,
        )
        return await self._request(req_def)

    # Flood API

    async def get_flood(
        self,
        *,
        latitude: float,
        longitude: float,
        daily: list[str] | None = None,
        ensemble: bool | None = None,
    ) -> flood_models.FloodResponse:
        """
        Get flood/river discharge forecast data.

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
        FloodResponse
            The parsed flood forecast data.
        """
        req_def = flood_service.get_flood(
            latitude=latitude,
            longitude=longitude,
            daily=daily,
            ensemble=ensemble,
        )
        return await self._request(req_def)

    # Ensemble API

    async def get_ensemble(
        self,
        *,
        latitude: float,
        longitude: float,
        models: list[str],
        hourly: list[str] | None = None,
    ) -> ensemble_models.EnsembleResponse:
        """
        Get ensemble forecast data for probabilistic forecasting.

        Parameters
        ----------
        latitude : float
            WGS84 Latitude.
        longitude : float
            WGS84 Longitude.
        models : list[str]
            Target ensemble model(s) (e.g. ["icon_seamless"]).
        hourly : list[str], optional
            Variables to retrieve.

        Returns
        -------
        EnsembleResponse
            The parsed ensemble data.
        """
        req_def = ensemble_service.get_ensemble(
            latitude=latitude,
            longitude=longitude,
            models_=models,
            hourly=hourly,
        )
        return await self._request(req_def)

    # Climate API

    async def get_climate(
        self,
        *,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        models: list[str] | None = None,
        daily: list[str] | None = None,
    ) -> climate_models.ClimateResponse:
        """
        Get long-term climate projection data.

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
        models : list[str], optional
            CMIP6 models (e.g. ["EC_Earth3P_HR"]).
        daily : list[str], optional
            Daily climate variables.

        Returns
        -------
        ClimateResponse
            The parsed climate data.
        """
        req_def = climate_service.get_climate(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            models_=models,
            daily=daily,
        )
        return await self._request(req_def)
