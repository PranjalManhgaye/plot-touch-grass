"""Open-Meteo weather client — free, no API key, open data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

from backend.labels import daylight_hours, days_since_last_frost, label_outdoor_action

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def _get_json(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    import asyncio

    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code in (429, 503, 502):
                await asyncio.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            last_exc = exc
            await asyncio.sleep(2 ** attempt)
    raise last_exc or RuntimeError("Open-Meteo request failed")


def _clamp_soil(value: float | None) -> float:
    if value is None:
        return 0.45
    return max(0.1, min(0.95, value))


async def fetch_today_conditions(lat: float, lon: float) -> dict[str, Any]:
    """Live conditions for a lat/lon using Open-Meteo forecast + recent archive."""
    today = date.today()
    frost_start = today - timedelta(days=120)

    async with httpx.AsyncClient(timeout=45.0) as client:
        forecast = await _get_json(
            client,
            FORECAST_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "timezone": "auto",
                "forecast_days": 1,
                "current": "temperature_2m,wind_speed_10m",
                "daily": (
                    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
                    "precipitation_sum,wind_speed_10m_max"
                ),
                "hourly": "soil_moisture_0_to_7cm",
            },
        )
        archive = await _get_json(
            client,
            ARCHIVE_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "start_date": frost_start.isoformat(),
                "end_date": today.isoformat(),
                "timezone": "auto",
                "daily": "temperature_2m_min",
            },
        )

    daily = forecast.get("daily", {})
    avg_temp = float(daily["temperature_2m_mean"][0])
    min_temp = float(daily["temperature_2m_min"][0])
    precip = float(daily["precipitation_sum"][0] or 0.0)
    wind = float(daily["wind_speed_10m_max"][0] or 0.0)

    hourly = forecast.get("hourly", {})
    soil_vals = hourly.get("soil_moisture_0_to_7cm") or []
    soil_raw = soil_vals[12] if len(soil_vals) > 12 else None
    soil = _clamp_soil(float(soil_raw) if soil_raw is not None else None)

    archive_mins = [
        float(x) for x in archive.get("daily", {}).get("temperature_2m_min", []) if x is not None
    ]
    frost_lag = days_since_last_frost(archive_mins)[-1] if archive_mins else 30
    if frost_lag > 365:
        frost_lag = 90

    doy = today.timetuple().tm_yday
    daylight = daylight_hours(doy, lat)

    return {
        "lat": lat,
        "lon": lon,
        "avg_temp_c": round(avg_temp, 2),
        "min_temp_c": round(min_temp, 2),
        "precip_mm": round(precip, 2),
        "wind_kmh": round(wind, 2),
        "soil_moisture": round(soil, 3),
        "days_since_last_frost": int(frost_lag),
        "day_of_year": doy,
        "daylight_h": round(daylight, 2),
        "source": "Open-Meteo (ERA5 reanalysis + forecast)",
        "location_label": None,
        "suggested_action": label_outdoor_action(
            avg_temp_c=avg_temp,
            min_temp_c=min_temp,
            precip_mm=precip,
            wind_kmh=wind,
            soil_moisture=soil,
            days_since_last_frost=frost_lag,
            daylight_h=daylight,
        ),
    }
