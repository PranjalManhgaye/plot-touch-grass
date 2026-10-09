# Data sources

## Training table (`outdoor_history.csv`)

| Field | Source |
|-------|--------|
| Temperature, precipitation, wind | [Open-Meteo Historical API](https://open-meteo.com/en/docs/historical-weather-api) — ERA5 reanalysis |
| Soil moisture | Open-Meteo hourly `soil_moisture_0_to_7cm` (noon sample) |
| Daylight | Astronomical calculation from latitude + day-of-year |
| Days since last frost | Derived from daily min temp ≤ 0 °C in the same series |
| `action` label | Documented heuristics in `backend/labels.py` (frost-free window, precip, wind) |

**Coverage:** 12 US cities, daily rows from 2018-01-01 through 2024-12-31 (~30,684 rows).

Regenerate:

```bash
python scripts/fetch_real_data.py
```

## Live weather (`/api/weather`)

[Open-Meteo Forecast API](https://open-meteo.com/en/docs) for today's conditions + 120-day archive for frost lag.

No API keys. Open data.
