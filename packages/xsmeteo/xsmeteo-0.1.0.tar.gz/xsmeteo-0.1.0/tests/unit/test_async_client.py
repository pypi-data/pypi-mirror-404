from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from xsmeteo.client.async_client import AsyncXSMeteo
from xsmeteo.exceptions import DecodeError, HTTPError
from xsmeteo.models.forecast import ForecastResponse
from xsmeteo.models.historical import HistoricalResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest.fixture
async def client() -> AsyncGenerator[AsyncXSMeteo, None]:
    async with AsyncXSMeteo() as client:
        # Mock the internal httpx client
        client._client = AsyncMock(spec=httpx.AsyncClient)
        yield client


@pytest.mark.asyncio
async def test_get_forecast_success(client: AsyncXSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = (
        b'{"latitude": 52.52, "longitude": 13.41, "generationtime_ms": 2.2, '
        b'"utc_offset_seconds": 0, "timezone": "GMT", "timezone_abbreviation": "GMT", '
        b'"elevation": 38.0}'
    )
    cast("AsyncMock", client._client.get).return_value = mock_response

    # Act
    result = await client.get_forecast(latitude=52.52, longitude=13.41)

    # Assert
    assert isinstance(result, ForecastResponse)
    assert result.latitude == 52.52
    assert result.longitude == 13.41
    cast("AsyncMock", client._client.get).assert_called_once()


@pytest.mark.asyncio
async def test_get_historical_success(client: AsyncXSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = (
        b'{"latitude": 52.52, "longitude": 13.41, "generationtime_ms": 2.2, '
        b'"utc_offset_seconds": 0, "timezone": "GMT", "timezone_abbreviation": "GMT", '
        b'"elevation": 38.0}'
    )
    cast("AsyncMock", client._client.get).return_value = mock_response

    # Act
    result = await client.get_historical(
        latitude=52.52, longitude=13.41, start_date="2022-01-01", end_date="2022-01-02"
    )

    # Assert
    assert isinstance(result, HistoricalResponse)
    assert result.latitude == 52.52
    cast("AsyncMock", client._client.get).assert_called_once()


@pytest.mark.asyncio
async def test_get_forecast_http_error(client: AsyncXSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.content = b'{"error": true, "reason": "Invalid parameters"}'
    mock_response.text = '{"error": true, "reason": "Invalid parameters"}'
    cast("AsyncMock", client._client.get).return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPError) as exc_info:
        await client.get_forecast(latitude=52.52, longitude=13.41)

    assert str(exc_info.value) == "400: Invalid parameters"
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_forecast_decode_error(client: AsyncXSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = b"invalid json"
    cast("AsyncMock", client._client.get).return_value = mock_response

    # Act & Assert
    with pytest.raises(DecodeError):
        await client.get_forecast(latitude=52.52, longitude=13.41)


@pytest.mark.asyncio
async def test_search_locations_success(client: AsyncXSMeteo) -> None:
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = (
        b'{"results": [{"id": 1, "name": "Berlin", "latitude": 52.52, "longitude": 13.41}]}'
    )
    cast("AsyncMock", client._client.get).return_value = mock_response

    # Act
    result = await client.search_locations(name="Berlin")

    # Assert
    assert result.results is not None
    assert len(result.results) == 1
    assert result.results[0].name == "Berlin"
