"""Regenerate data/outdoor_history.csv (deterministic)."""

from __future__ import annotations

import csv
import math
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "outdoor_history.csv"


def main() -> None:
    random.seed(42)
    rows = []
    climates = [
        ("cool", 45.5, -122.6, 100, 8),
        ("temperate", 40.7, -74.0, 85, 12),
        ("mild", 34.0, -118.2, 40, 16),
        ("warm", 29.7, -95.3, 20, 20),
        ("continental", 41.8, -87.6, 110, 10),
    ]
    actions = ["wait", "walk", "garden"]

    for climate, lat, lon, frost_mean, temp_base in climates:
        for _year in range(2018, 2025):
            for doy in range(1, 366, 3):
                season = math.sin(2 * math.pi * (doy - 80) / 365)
                avg_temp = temp_base + 12 * season + random.uniform(-3, 3)
                min_temp = avg_temp - random.uniform(3, 8)
                precip = max(0, random.gauss(2.5 if season > 0 else 1.2, 2.0))
                daylight = 10 + 4 * math.sin(2 * math.pi * (doy - 80) / 365)
                wind = abs(random.gauss(8, 4))
                soil_moisture = max(
                    0.1,
                    min(
                        0.95,
                        0.45 + precip / 20 - avg_temp / 80 + random.uniform(-0.1, 0.1),
                    ),
                )
                days_since_frost = doy - frost_mean + random.randint(-10, 10)
                frost_risk = 1 / (1 + math.exp((min_temp - 2) / 2))

                if min_temp < 1 or frost_risk > 0.65 or avg_temp < 5:
                    action = "wait"
                elif precip > 8 or wind > 18 or avg_temp > 34:
                    action = "walk" if daylight > 9 else "wait"
                elif (
                    days_since_frost > 14
                    and 8 <= avg_temp <= 28
                    and soil_moisture > 0.25
                    and precip < 6
                ):
                    action = "garden"
                elif daylight > 10 and 6 <= avg_temp <= 30:
                    action = "walk"
                else:
                    action = "wait"

                if random.random() < 0.05:
                    action = random.choice(actions)

                rows.append(
                    {
                        "lat": round(lat + random.uniform(-0.4, 0.4), 4),
                        "lon": round(lon + random.uniform(-0.4, 0.4), 4),
                        "climate_band": climate,
                        "day_of_year": doy,
                        "avg_temp_c": round(avg_temp, 2),
                        "min_temp_c": round(min_temp, 2),
                        "precip_mm": round(precip, 2),
                        "daylight_h": round(daylight, 2),
                        "wind_kmh": round(wind, 2),
                        "soil_moisture": round(soil_moisture, 3),
                        "days_since_last_frost": days_since_frost,
                        "action": action,
                    }
                )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows → {OUT}")
    print(Counter(r["action"] for r in rows))


if __name__ == "__main__":
    main()
