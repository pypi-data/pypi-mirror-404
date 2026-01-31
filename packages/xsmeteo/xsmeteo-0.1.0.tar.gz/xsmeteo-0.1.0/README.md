<div align="center">
    <h1>xsmeteo<h1>

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

**High-performance, strictly typed Python wrapper for the [Open-Meteo API](https://open-meteo.com/).**

## Features

- 🚀 **High Performance** – Uses `msgspec` for maximum serialization speed
- 🔒 **100% Type Safe** – Full static typing with `mypy --strict` compliance
- 🔄 **Sync & Async** – Both synchronous and asynchronous clients
- ⏱️ **Built-in Rate Limiting** – Hierarchical token bucket respecting Open-Meteo limits
- 🌍 **Full API Coverage** – All 9 Open-Meteo endpoints supported

## Installation

```bash
pip install xsmeteo
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add xsmeteo
```

## Quick Start

### Synchronous Usage

```python
from xsmeteo import XSMeteo

with XSMeteo() as client:
    # Get weather forecast
    forecast = client.get_forecast(
        latitude=52.52,
        longitude=13.41,
        hourly=["temperature_2m", "rain"],
        timezone="auto",
    )
    print(forecast)
```

### Asynchronous Usage

```python
import asyncio
from xsmeteo import AsyncXSMeteo

async def main():
    async with AsyncXSMeteo() as client:
        forecast = await client.get_forecast(
            latitude=52.52,
            longitude=13.41,
            hourly=["temperature_2m"],
        )
        print(forecast)

asyncio.run(main())
```

## API Coverage

| Endpoint | Method | Description |
|----------|--------|-------------|
| **Forecast** | `get_forecast()` | Current weather and up to 16-day forecast |
| **Historical** | `get_historical()` | Decades of historical weather data (ERA5) |
| **Marine** | `get_marine()` | Oceanographic data (waves, currents) |
| **Air Quality** | `get_air_quality()` | Pollutants and pollen forecasts |
| **Geocoding** | `search_locations()` | Forward geocoding (name to coordinates) |
| **Elevation** | `get_elevation()` | Altitude data for coordinates |
| **Flood** | `get_flood()` | River discharge and flood forecasts |
| **Ensemble** | `get_ensemble()` | Probabilistic ensemble forecasts |
| **Climate** | `get_climate()` | Long-term climate projections (CMIP6) |

## Rate Limiting

xsmeteo includes built-in rate limiting that respects Open-Meteo's fair use policy:

| Limit | Value |
|-------|-------|
| Minutely | ~600 requests |
| Hourly | ~5,000 requests |
| Daily | ~10,000 requests |

Custom limits can be configured:

```python
from xsmeteo import XSMeteo, RateLimitConfig

custom_limits = [
    RateLimitConfig(limit=100, period_seconds=60.0),  # 100/min
]

client = XSMeteo(rate_limits=custom_limits)
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Attribution

This library uses the [Open-Meteo API](https://open-meteo.com/) under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).
