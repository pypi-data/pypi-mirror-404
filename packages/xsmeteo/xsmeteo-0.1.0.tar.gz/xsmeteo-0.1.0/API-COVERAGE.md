# Open-Meteo API Coverage Analysis

## 1. System Overview

The Open-Meteo API is a high-performance, open-access interface for retrieving global weather data. It aggregates data from multiple national weather services (NOAA, DWD, MeteoFrance, etc.) and provides it through a unified RESTful API.

- **Architecture**: Coordinate-based system using WGS84 (latitude/longitude) referencing.
- **Request Method**: Strictly **GET** requests. All parameters are encoded in the URL query string.
- **Response Format**: JSON (default) with optional FlatBuffers/Protobuf support for high-throughput applications.
- **Base URLs**:
  - `api.open-meteo.com` (Weather Forecast)
  - `archive-api.open-meteo.com` (Historical)
  - `marine-api.open-meteo.com` (Marine)
  - `air-quality-api.open-meteo.com` (Air Quality)
  - `geocoding-api.open-meteo.com` (Geocoding)
  - `elevation-api.open-meteo.com` (Elevation)
  - `flood-api.open-meteo.com` (Flood)
  - `ensemble-api.open-meteo.com` (Ensemble)
  - `climate-api.open-meteo.com` (Climate Change)

## 2. Operational Constraints

### Rate Limits & Fair Use

The Open-Meteo API operates on a "Fair Use" policy for its free tier, designed for non-commercial, open-source, and private projects.

| Metric | Limit (Free Tier) |
| :--- | :--- |
| **Minutely** | ~600 calls |
| **Hourly** | ~5,000 calls |
| **Daily** | ~10,000 calls |
| **Concurrency** | Limited (avoid parallel requests) |

- **Commercial Use**: Requires a commercial license if the application is commercial or exceeds the free limits.
- **Attribution**: **Required**. You must link back to `https://open-meteo.com/` under the CC-BY 4.0 license.

### Error Codes

Errors are returned as standard HTTP status codes with a JSON body explaining the failure.

- **400 Bad Request**: Malformed parameters (e.g., missing `latitude`/`longitude`, out-of-range values).
- **Error JSON Structure**:

    ```json
    {
      "error": true,
      "reason": "Latitude must be in range of -90 to 90°."
    }
    ```

## 3. Endpoint Coverage

### 3.1 Weather Forecast API

**URL**: `https://api.open-meteo.com/v1/forecast`
**Purpose**: The core endpoint for current weather, hourly forecasts (up to 16 days), and daily aggregations.

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `hourly` | No | String[] | - | Comma-separated list of hourly variables (e.g., `temperature_2m`). |
| `daily` | No | String[] | - | Comma-separated list of daily variables (e.g., `temperature_2m_max`). |
| `current` | No | String[] | - | Current weather variables. |
| `temperature_unit` | No | String | `celsius` | `celsius` or `fahrenheit`. |
| `wind_speed_unit` | No | String | `kmh` | `kmh`, `ms`, `mph`, `kn`. |
| `precipitation_unit`| No | String | `mm` | `mm` or `inch`. |
| `timeformat` | No | String | `iso8601` | `iso8601` or `unixtime`. |
| `timezone` | No | String | `GMT` | Timezone identifier (e.g., `Europe/London`) or `auto`. |
| `past_days` | No | Integer | `0` | Days of past data to include (0-92). |
| `forecast_days` | No | Integer | `7` | Days of forecast to return (1-16). |
| `models` | No | String[] | `auto` | Specific weather models (e.g., `icon_d2`, `gfs`). |

#### Response Format

Returns a JSON object divided by time resolution (`hourly`, `daily`).

```json
{
  "latitude": 52.52,
  "longitude": 13.41,
  "hourly_units": { "temperature_2m": "°C" },
  "hourly": {
    "time": ["2024-01-01T00:00", ...],
    "temperature_2m": [10.5, ...]
  }
}
```

---

### 3.2 Historical Weather API

**URL**: `https://archive-api.open-meteo.com/v1/archive`
**Purpose**: Retrieves decades of historical weather data using reanalysis models (ERA5).

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `start_date` | **Yes** | String | - | Start date (YYYY-MM-DD). |
| `end_date` | **Yes** | String | - | End date (YYYY-MM-DD). |
| `hourly` | No | String[] | - | Historical hourly variables. |
| `daily` | No | String[] | - | Historical daily variables. |
| `models` | No | String | `best_match` | Reanalysis model selector. |
| `timezone` | No | String | `GMT` | Timezone for time alignment. |

#### Response Format

Identical structure to the Forecast API, centered on the requested date range.

---

### 3.3 Marine Weather API

**URL**: `https://marine-api.open-meteo.com/v1/marine`
**Purpose**: Specialized oceanographic data (waves, currents) for maritime applications.

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `hourly` | No | String[] | - | Variables: `wave_height`, `wave_direction`, etc. |
| `daily` | No | String[] | - | Variables: `wave_height_max`, etc. |
| `timezone` | No | String | `UTC` | Timezone setting. |
| `cell_selection` | No | String | `sea` | `sea`, `land`, or `nearest`. Ensures data is fetched from water cells. |

#### Response Format

Standard JSON structure. Beware that requesting marine data for inland coordinates without `cell_selection` adjustment may return nulls.

---

### 3.4 Air Quality API

**URL**: `https://air-quality-api.open-meteo.com/v1/air-quality`
**Purpose**: Forecasts for air pollutants (PM2.5, NO2, SO2, Ozone) and pollen levels.

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `hourly` | No | String[] | - | Pollutants (e.g., `pm10`, `birch_pollen`). |
| `domains` | No | String | `cams_global` | `cams_global` or `cams_europe` (higher resolution for EU). |
| `timezone` | No | String | `UTC` | Timezone setting. |

#### Response Format

Units typically in `μg/m³` for particles. Pollen counts are often in grains/m³.

---

### 3.5 Geocoding API

**URL**: `https://geocoding-api.open-meteo.com/v1/search`
**Purpose**: Resolves location names to coordinates (Forward Geocoding).

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | **Yes** | String | - | Name of the city/place (min 2 chars). |
| `count` | No | Integer | `10` | Number of results to return. |
| `language` | No | String | `en` | Language for result names. |
| `format` | No | String | `json` | Response format. |

#### Response Format

Returns a `results` array containing location objects with `id`, `name`, `latitude`, `longitude`, `country_code`, and `timezone`.

---

### 3.6 Elevation API

**URL**: `https://api.open-meteo.com/v1/elevation`
**Purpose**: Returns altitude data for given coordinates using DEM (Digital Elevation Models).

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float/Array | - | Single or comma-separated latitudes. |
| `longitude` | **Yes** | Float/Array | - | Single or comma-separated longitudes. |

#### Response Format

```json
{
  "elevation": [512.0, 105.5]
}
```

---

### 3.7 Flood API

**URL**: `https://flood-api.open-meteo.com/v1/flood`
**Purpose**: River discharge and flood forecasting via GloFAS.

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `daily` | No | String[] | - | `river_discharge`, `river_discharge_mean`. |
| `ensemble` | No | Boolean | `false` | If true, returns all 51 ensemble members. |

#### Response Format

Standard JSON with `daily` arrays. Discharge typically in `m³/s`.

---

### 3.8 Ensemble API

**URL**: `https://ensemble-api.open-meteo.com/v1/ensemble`
**Purpose**: Access to raw ensemble members for probabilistic forecasting.

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `models` | **Yes** | String[] | - | Target ensemble model (e.g., `icon_seamless`). |
| `hourly` | No | String[] | - | Variables to retrieve. |

#### Response Format

Includes standard summary statistics (mean, spread) plus individual member streams (e.g., `temperature_member01`, `temperature_member02`, ...).

---

### 3.9 Climate Change API

**URL**: `https://climate-api.open-meteo.com/v1/climate`
**Purpose**: Long-term climate projections (1950-2050) based on CMIP6 models.

#### Parameters

| Parameter | Required | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | **Yes** | Float | - | WGS84 Latitude. |
| `longitude` | **Yes** | Float | - | WGS84 Longitude. |
| `start_date` | **Yes** | String | - | e.g. `1950-01-01`. |
| `end_date` | **Yes** | String | - | e.g. `2050-12-31`. |
| `models` | No | String[] | All | CMIP6 models (e.g., `EC_Earth3P_HR`). |

#### Response Format

Daily resolution climate data over long periods.

## 4. Best Practices

### 4.1 URL Construction & Efficiency

- **Comma-Separated Values**: For `hourly` and `daily` parameters, always use comma-separated strings (e.g., `&hourly=temperature_2m,rain`) rather than repeating parameters.
- **Bulk Requests**: Some APIs (like Elevation) support multiple coordinates in a single request (e.g., `?latitude=52.52,48.85&longitude=13.41,2.35`). Use this to reduce HTTP overhead.
- **Parameter Order**: Keep `latitude` and `longitude` first for readability, though the API is order-agnostic.

### 4.2 Timezone Handling

- **Use `auto`**: For user-facing applications, setting `&timezone=auto` allows the API to automatically resolve the local time for the requested coordinates.
- **UTC for Backend**: For data storage or server-side processing, explicitly set `&timezone=UTC` (or omit it, as it defaults to GMT) to avoid ambiguity.
- **ISO 8601**: Stick to `&timeformat=iso8601` (default) for maximum compatibility.

### 4.3 Data Precision & Units

- **Explicit Units**: Always explicitly define `temperature_unit`, `wind_speed_unit`, and `precipitation_unit` if your application targets a specific locale (e.g., USA). Do not rely on defaults if your user base is global.
- **Bitmasking**: The `weather_code` parameter is a highly efficient integer representation of weather states (WMO codes). Prefer storing/transmitting this over text strings.
