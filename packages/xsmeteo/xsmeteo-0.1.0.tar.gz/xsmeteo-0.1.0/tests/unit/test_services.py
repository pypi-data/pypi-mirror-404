from __future__ import annotations

from xsmeteo.services import (
    air_quality,
    climate,
    elevation,
    ensemble,
    flood,
    forecast,
    geocoding,
    historical,
    marine,
)


def test_forecast_service_defaults() -> None:
    req = forecast.get_forecast(latitude=52.52, longitude=13.41)

    assert req.url == "https://api.open-meteo.com/v1/forecast"
    assert req.params["latitude"] == 52.52
    assert req.params["longitude"] == 13.41
    assert req.params["hourly"] is None
    assert req.params["daily"] is None


def test_forecast_service_full() -> None:
    req = forecast.get_forecast(
        latitude=52.52,
        longitude=13.41,
        hourly=["temp_2m"],
        daily=["rain_sum"],
        temperature_unit="fahrenheit",
        forecast_days=3,
    )

    assert req.params["hourly"] == ["temp_2m"]
    assert req.params["daily"] == ["rain_sum"]
    assert req.params["temperature_unit"] == "fahrenheit"
    assert req.params["forecast_days"] == 3


def test_historical_service() -> None:
    req = historical.get_historical(
        latitude=52.52,
        longitude=13.41,
        start_date="2022-01-01",
        end_date="2022-01-02",
        hourly=["temp_2m"],
    )

    assert req.url == "https://archive-api.open-meteo.com/v1/archive"
    assert req.params["start_date"] == "2022-01-01"
    assert req.params["end_date"] == "2022-01-02"
    assert req.params["hourly"] == ["temp_2m"]


def test_marine_service() -> None:
    req = marine.get_marine(latitude=52.52, longitude=13.41, hourly=["wave_height"])

    assert req.url == "https://marine-api.open-meteo.com/v1/marine"
    assert req.params["hourly"] == ["wave_height"]


def test_air_quality_service() -> None:
    req = air_quality.get_air_quality(latitude=52.52, longitude=13.41, hourly=["pm10"])

    assert req.url == "https://air-quality-api.open-meteo.com/v1/air-quality"
    assert req.params["hourly"] == ["pm10"]


def test_geocoding_service() -> None:
    req = geocoding.search_locations(name="London", count=5, language="fr")

    assert req.url == "https://geocoding-api.open-meteo.com/v1/search"
    assert req.params["name"] == "London"
    assert req.params["count"] == 5
    assert req.params["language"] == "fr"


def test_elevation_service() -> None:
    req = elevation.get_elevation(latitude=52.52, longitude=13.41)

    assert req.url == "https://api.open-meteo.com/v1/elevation"
    assert req.params["latitude"] == "52.52"
    assert req.params["longitude"] == "13.41"


def test_flood_service() -> None:
    req = flood.get_flood(latitude=52.52, longitude=13.41, daily=["river_discharge"])

    assert req.url == "https://flood-api.open-meteo.com/v1/flood"
    assert req.params["daily"] == ["river_discharge"]


def test_ensemble_service() -> None:
    req = ensemble.get_ensemble(latitude=52.52, longitude=13.41, models_=["icon_seamless"])

    assert req.url == "https://ensemble-api.open-meteo.com/v1/ensemble"
    assert req.params["models"] == ["icon_seamless"]


def test_climate_service() -> None:
    req = climate.get_climate(
        latitude=52.52,
        longitude=13.41,
        start_date="2020-01-01",
        end_date="2050-01-01",
        models_=["CMCC_CM2_VHR4"],
    )

    assert req.url == "https://climate-api.open-meteo.com/v1/climate"
    assert req.params["models"] == ["CMCC_CM2_VHR4"]
