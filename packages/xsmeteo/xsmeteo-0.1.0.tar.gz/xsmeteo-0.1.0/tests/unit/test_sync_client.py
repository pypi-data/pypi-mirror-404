from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

import httpx
import pytest

from xsmeteo.client.sync_client import XSMeteo
from xsmeteo.exceptions import DecodeError, HTTPError
from xsmeteo.models.forecast import ForecastResponse
from xsmeteo.models.historical import HistoricalResponse

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def client() -> Generator[XSMeteo, None, None]:
    with XSMeteo() as client:
        # Mock the internal httpx client
        client._client = MagicMock(spec=httpx.Client)
        yield client


def test_get_forecast_success(client: XSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = (
        b'{"latitude": 52.52, "longitude": 13.41, "generationtime_ms": 2.2, '
        b'"utc_offset_seconds": 0, "timezone": "GMT", "timezone_abbreviation": "GMT", '
        b'"elevation": 38.0}'
    )
    cast("MagicMock", client._client.get).return_value = mock_response

    # Act
    result = client.get_forecast(latitude=52.52, longitude=13.41)

    # Assert
    assert isinstance(result, ForecastResponse)
    assert result.latitude == 52.52
    assert result.longitude == 13.41
    cast("MagicMock", client._client.get).assert_called_once()


def test_get_historical_success(client: XSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = (
        b'{"latitude": 52.52, "longitude": 13.41, "generationtime_ms": 2.2, '
        b'"utc_offset_seconds": 0, "timezone": "GMT", "timezone_abbreviation": "GMT", '
        b'"elevation": 38.0}'
    )
    cast("MagicMock", client._client.get).return_value = mock_response

    # Act
    result = client.get_historical(
        latitude=52.52, longitude=13.41, start_date="2022-01-01", end_date="2022-01-02"
    )

    # Assert
    assert isinstance(result, HistoricalResponse)
    assert result.latitude == 52.52
    cast("MagicMock", client._client.get).assert_called_once()


def test_get_forecast_http_error(client: XSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.content = b'{"error": true, "reason": "Invalid parameters"}'
    mock_response.text = '{"error": true, "reason": "Invalid parameters"}'
    cast("MagicMock", client._client.get).return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPError) as exc_info:
        client.get_forecast(latitude=52.52, longitude=13.41)

    assert str(exc_info.value) == "400: Invalid parameters"
    assert exc_info.value.status_code == 400


def test_get_forecast_decode_error(client: XSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = b"invalid json"
    cast("MagicMock", client._client.get).return_value = mock_response

    # Act & Assert
    with pytest.raises(DecodeError):
        client.get_forecast(latitude=52.52, longitude=13.41)


def test_search_locations_success(client: XSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = (
        b'{"results": [{"id": 1, "name": "Berlin", "latitude": 52.52, "longitude": 13.41}]}'
    )
    cast("MagicMock", client._client.get).return_value = mock_response

    # Act
    result = client.search_locations(name="Berlin")

    # Assert
    assert result.results is not None
    assert len(result.results) == 1
    assert result.results[0].name == "Berlin"
