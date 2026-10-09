from __future__ import annotations

import math
import os
import threading
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.checklist import VERDICTS, build_checklist
from backend.engine import FEATURE_COLS, engine
from backend.locations import LOCATIONS
from backend.weather import fetch_today_conditions

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

app = FastAPI(title="PLOT", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CheckRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    avg_temp_c: float = Field(..., ge=-40, le=50)
    min_temp_c: float = Field(..., ge=-45, le=45)
    precip_mm: float = Field(0, ge=0, le=200)
    wind_kmh: float = Field(8, ge=0, le=120)
    soil_moisture: float = Field(0.45, ge=0, le=1)
    days_since_last_frost: int = Field(30, ge=-60, le=365)
    day_of_year: int | None = Field(None, ge=1, le=366)
    daylight_h: float | None = Field(None, ge=0, le=24)


class PlacePreset(BaseModel):
    id: str
    label: str
    region: str
    lat: float
    lon: float


PRESETS = [
    PlacePreset(id=loc.id, label=loc.label, region=loc.region, lat=loc.lat, lon=loc.lon)
    for loc in LOCATIONS
]


def _daylight_hours(doy: int, lat: float) -> float:
    """Approximate daylight hours from day-of-year and latitude."""
    decl = 23.44 * math.sin(math.radians((360 / 365) * (doy - 81)))
    lat_r = math.radians(lat)
    decl_r = math.radians(decl)
    arg = -math.tan(lat_r) * math.tan(decl_r)
    arg = max(-1.0, min(1.0, arg))
    ha = math.acos(arg)
    return 24 * ha / math.pi


@app.on_event("startup")
def startup() -> None:
    threading.Thread(target=engine.load, name="plot-model-load", daemon=True).start()


@app.get("/api/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, **engine.stats()}


@app.get("/api/presets")
def presets() -> list[PlacePreset]:
    return PRESETS


@app.get("/api/weather")
async def weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
) -> dict:
    """Today's real conditions from Open-Meteo for the given coordinates."""
    try:
        return await fetch_today_conditions(lat, lon)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Open-Meteo request failed: {exc}") from exc


@app.post("/api/check")
def check(body: CheckRequest) -> dict:
    try:
        engine.ensure_ready()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not engine.ready:
        raise HTTPException(
            status_code=503,
            detail=engine.error or "Model is still loading — retry in a few seconds.",
        )

    doy = body.day_of_year or date.today().timetuple().tm_yday
    daylight = body.daylight_h if body.daylight_h is not None else _daylight_hours(doy, body.lat)

    features = {
        "lat": body.lat,
        "lon": body.lon,
        "day_of_year": float(doy),
        "avg_temp_c": body.avg_temp_c,
        "min_temp_c": body.min_temp_c,
        "precip_mm": body.precip_mm,
        "daylight_h": daylight,
        "wind_kmh": body.wind_kmh,
        "soil_moisture": body.soil_moisture,
        "days_since_last_frost": float(body.days_since_last_frost),
    }

    missing = [c for c in FEATURE_COLS if c not in features]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing features: {missing}")

    result = engine.predict(features)
    verdict = VERDICTS.get(result.action, VERDICTS["wait"])
    checklist = build_checklist(result.action, features)

    return {
        "action": result.action,
        "confidence": round(result.confidence, 4),
        "probabilities": {k: round(v, 4) for k, v in result.probabilities.items()},
        "verdict": verdict,
        "checklist": checklist,
        "features_used": features,
        "engine": result.engine,
        "model_note": result.model_note,
    }


web_dir = ROOT / "web"
if web_dir.exists():
    app.mount("/assets", StaticFiles(directory=web_dir), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(web_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
