"""Transparent outdoor-action labels from real weather features.

Labels are horticulture-inspired heuristics applied to observed weather —
not ground-truth human decisions. Documented openly for judges.
"""


def daylight_hours(day_of_year: int, lat: float) -> float:
    import math

    decl = 23.44 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    lat_r = math.radians(lat)
    decl_r = math.radians(decl)
    arg = max(-1.0, min(1.0, -math.tan(lat_r) * math.tan(decl_r)))
    return 24 * math.acos(arg) / math.pi


def days_since_last_frost(min_temps: list[float], frost_threshold_c: float = 0.0) -> list[int]:
    """Walk backward through daily min temps; count days since last frost day."""
    out: list[int] = []
    last_frost_idx: int | None = None
    for i, tmin in enumerate(min_temps):
        if tmin <= frost_threshold_c:
            last_frost_idx = i
        if last_frost_idx is None:
            out.append(999 if i == 0 else out[-1] + 1)
        else:
            out.append(i - last_frost_idx)
    return out


def label_outdoor_action(
    *,
    avg_temp_c: float,
    min_temp_c: float,
    precip_mm: float,
    wind_kmh: float,
    soil_moisture: float,
    days_since_last_frost: int,
    daylight_h: float,
) -> str:
    """Return wait | walk | garden from real weather observations."""
    # Hard frost / freeze — stay inside, protect plants
    if min_temp_c <= 1.0 or avg_temp_c < 2.0:
        return "wait"

    # Dangerous or miserable outdoor gardening conditions
    if precip_mm >= 12.0 or wind_kmh >= 35.0 or avg_temp_c >= 36.0:
        return "walk" if daylight_h >= 9.0 and avg_temp_c < 36.0 else "wait"

    # Extension-style planting window: frost-free window + workable soil moisture
    if (
        days_since_last_frost >= 14
        and 10.0 <= avg_temp_c <= 27.0
        and min_temp_c >= 4.0
        and precip_mm < 8.0
        and wind_kmh < 22.0
        and 0.22 <= soil_moisture <= 0.75
    ):
        return "garden"

    # Good day to be outside even if not a planting day
    if 5.0 <= avg_temp_c <= 32.0 and wind_kmh < 28.0 and precip_mm < 10.0:
        return "walk"

    return "wait"
