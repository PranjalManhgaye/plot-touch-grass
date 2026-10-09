#!/usr/bin/env python3
"""Download real daily weather from Open-Meteo and build outdoor_history.csv.

Data: Open-Meteo Historical Weather API (ERA5 reanalysis).
Labels: transparent horticulture heuristics in backend/labels.py — not synthetic noise.
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.labels import daylight_hours, days_since_last_frost, label_outdoor_action
from backend.locations import LOCATIONS

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2018-01-01"
END_DATE = "2024-12-31"
OUT_PATH = ROOT / "data" / "outdoor_history.csv"


def fetch_city(client: httpx.Client, loc) -> list[dict]:
    print(f"  fetching {loc.label} …", flush=True)
    resp = client.get(
        ARCHIVE_URL,
        params={
            "latitude": loc.lat,
            "longitude": loc.lon,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "timezone": "auto",
            "daily": (
                "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
                "precipitation_sum,wind_speed_10m_max"
            ),
            "hourly": "soil_moisture_0_to_7cm",
        },
    )
    resp.raise_for_status()
    payload = resp.json()
    daily = payload["daily"]
    dates = daily["time"]
    mins = [float(x) for x in daily["temperature_2m_min"]]
    frost_lags = days_since_last_frost(mins)

    # Daily noon soil moisture from hourly (index 12 per day if hourly is contiguous)
    hourly_soil = payload.get("hourly", {}).get("soil_moisture_0_to_7cm") or []
    soil_by_day: dict[str, float] = {}
    hourly_times = payload.get("hourly", {}).get("time") or []
    for t, sm in zip(hourly_times, hourly_soil):
        if sm is None:
            continue
        day_key = t[:10]
        if t.endswith("T12:00"):
            soil_by_day[day_key] = float(sm)

    rows: list[dict] = []
    for i, day_str in enumerate(dates):
        doy = date.fromisoformat(day_str).timetuple().tm_yday
        avg_temp = float(daily["temperature_2m_mean"][i])
        min_temp = float(daily["temperature_2m_min"][i])
        precip = float(daily["precipitation_sum"][i] or 0.0)
        wind = float(daily["wind_speed_10m_max"][i] or 0.0)
        soil = soil_by_day.get(day_str, 0.45)
        soil = max(0.1, min(0.95, soil))
        daylight = daylight_hours(doy, loc.lat)
        frost_lag = frost_lags[i]
        if frost_lag > 365:
            frost_lag = 365

        action = label_outdoor_action(
            avg_temp_c=avg_temp,
            min_temp_c=min_temp,
            precip_mm=precip,
            wind_kmh=wind,
            soil_moisture=soil,
            days_since_last_frost=frost_lag,
            daylight_h=daylight,
        )

        rows.append(
            {
                "lat": loc.lat,
                "lon": loc.lon,
                "city": loc.label,
                "date": day_str,
                "day_of_year": doy,
                "avg_temp_c": round(avg_temp, 2),
                "min_temp_c": round(min_temp, 2),
                "precip_mm": round(precip, 2),
                "daylight_h": round(daylight, 2),
                "wind_kmh": round(wind, 2),
                "soil_moisture": round(soil, 3),
                "days_since_last_frost": frost_lag,
                "action": action,
            }
        )
    return rows


def main() -> None:
    all_rows: list[dict] = []
    with httpx.Client(timeout=120.0) as client:
        for loc in LOCATIONS:
            try:
                all_rows.extend(fetch_city(client, loc))
            except httpx.HTTPError as exc:
                print(f"  ERROR {loc.label}: {exc}", file=sys.stderr)
            time.sleep(1.0)  # polite pacing for Open-Meteo

    if not all_rows:
        raise SystemExit("No rows fetched — check network or API limits.")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(all_rows[0].keys())
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    from collections import Counter

    counts = Counter(r["action"] for r in all_rows)
    print(f"\nWrote {len(all_rows):,} rows → {OUT_PATH}")
    print("Label distribution:", dict(counts))
    print("Source: Open-Meteo ERA5 reanalysis (https://open-meteo.com)")


if __name__ == "__main__":
    main()
