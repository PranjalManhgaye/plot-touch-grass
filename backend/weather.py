"""Open-Meteo weather client — free, no API key, open data."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

import httpx

from pathlib import Path

import pandas as pd

from backend.labels import daylight_hours, days_since_last_frost, label_outdoor_action
from backend.locations import LOCATIONS

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "outdoor_history.csv"
_HISTORY_DF: pd.DataFrame | None = None
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_S = 20 * 60


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


async def _get_json(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    import asyncio

    last_status: int | None = None
    last_exc: Exception | None = None
    for attempt in range(5):
        try:
            resp = await client.get(url, params=params)
            last_status = resp.status_code
            if resp.status_code in (429, 503, 502):
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            last_exc = exc
            await asyncio.sleep(1.5 * (attempt + 1))
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Open-Meteo unavailable (last status {last_status})")


def _clamp_soil(value: float | None) -> float:
    if value is None:
        return 0.45
    return max(0.1, min(0.95, value))


def _history_df() -> pd.DataFrame:
    global _HISTORY_DF
    if _HISTORY_DF is None:
        _HISTORY_DF = pd.read_csv(HISTORY_PATH)
    return _HISTORY_DF


def _nearest_city(lat: float, lon: float):
    return min(LOCATIONS, key=lambda loc: (loc.lat - lat) ** 2 + (loc.lon - lon) ** 2)


def fallback_from_history(lat: float, lon: float) -> dict[str, Any]:
    """Real ERA5 row for nearest city + today's calendar day (2024 slice)."""
    city = _nearest_city(lat, lon)
    doy = date.today().timetuple().tm_yday
    df = _history_df()
    subset = df[(df["city"] == city.label) & (df["day_of_year"] == doy)]
    if subset.empty:
        subset = df[df["city"] == city.label].tail(1)
    row = subset.sort_values("date", ascending=False).iloc[0]

    avg_temp = float(row["avg_temp_c"])
    min_temp = float(row["min_temp_c"])
    precip = float(row["precip_mm"])
    wind = float(row["wind_kmh"])
    soil = float(row["soil_moisture"])
    frost_lag = int(row["days_since_last_frost"])
    daylight = float(row["daylight_h"])

    return {
        "lat": lat,
        "lon": lon,
        "avg_temp_c": round(avg_temp, 2),
        "min_temp_c": round(min_temp, 2),
        "precip_mm": round(precip, 2),
        "wind_kmh": round(wind, 2),
        "soil_moisture": round(soil, 3),
        "days_since_last_frost": frost_lag,
        "day_of_year": doy,
        "daylight_h": round(daylight, 2),
        "source": f"ERA5 table fallback — {city.label}, calendar day {doy} (row {row['date']})",
        "location_label": city.label,
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


def _estimate_frost_lag(min_temps: list[float], today_min: float) -> int:
    if min_temps:
        lag = days_since_last_frost(min_temps)[-1]
        if lag <= 365:
            return int(lag)
    # Fallback when archive slice is thin
    if today_min <= 0:
        return 0
    if today_min < 3:
        return 3
    return 45


async def fetch_today_conditions(lat: float, lon: float) -> dict[str, Any]:
    """Live conditions via one Open-Meteo forecast call (includes past_days for frost)."""
    key = _cache_key(lat, lon)
    cached = _CACHE.get(key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_S:
        return cached[1]

    today = date.today()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = await _get_json(
                client,
                FORECAST_URL,
                {
                    "latitude": lat,
                    "longitude": lon,
                    "timezone": "auto",
                    "forecast_days": 1,
                    "past_days": 92,
                    "daily": (
                        "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
                        "precipitation_sum,wind_speed_10m_max"
                    ),
                    "hourly": "soil_moisture_0_to_7cm",
                },
            )
    except Exception:
        result = fallback_from_history(lat, lon)
        _CACHE[key] = (time.time(), result)
        return result

    daily = payload.get("daily", {})
    times = daily.get("time") or []
    mins_series = [
        float(x) for x in daily.get("temperature_2m_min", []) if x is not None
    ]

    # Last day in series is today when past_days + forecast_days are included
    today_idx = len(times) - 1 if times else 0
    avg_temp = float(daily["temperature_2m_mean"][today_idx])
    min_temp = float(daily["temperature_2m_min"][today_idx])
    precip = float(daily["precipitation_sum"][today_idx] or 0.0)
    wind = float(daily["wind_speed_10m_max"][today_idx] or 0.0)

    hourly = payload.get("hourly", {})
    soil_vals = hourly.get("soil_moisture_0_to_7cm") or []
    soil_raw = next((v for v in reversed(soil_vals) if v is not None), None)
    soil = _clamp_soil(float(soil_raw) if soil_raw is not None else None)

    frost_lag = _estimate_frost_lag(mins_series, min_temp)
    doy = today.timetuple().tm_yday
    daylight = daylight_hours(doy, lat)

    result = {
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
        "source": "Open-Meteo forecast + 92-day frost window",
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
    _CACHE[key] = (time.time(), result)
    return result
