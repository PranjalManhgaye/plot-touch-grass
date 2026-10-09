# PLOT

**Leave the screen. Tend the ground.**

PLOT is a Hacktoberfest Week 1 (*Touch Grass*) project. It uses **Prior Labs TabPFN** on **real weather data** (Open-Meteo ERA5) to classify today’s outdoor action as **wait**, **walk**, or **garden** — then gives a short checklist meant to end at your door.

## Live demo

- **App:** https://plot-touch-grass.onrender.com
- **Repo:** https://github.com/PranjalManhgaye/plot-touch-grass

Pick a city or use your location → live weather loads → TabPFN predicts → go outside.

## Real data (not synthetic)

| What | Source |
|------|--------|
| Training rows | **30,684** daily observations, 12 US cities, 2018–2024 |
| Weather | [Open-Meteo](https://open-meteo.com) ERA5 reanalysis |
| Frost lag | Computed from real daily min temps ≤ 0 °C |
| Labels | Transparent horticulture heuristics (`backend/labels.py`) |
| Live inputs | Open-Meteo forecast + 120-day archive |

See `data/DATA_SOURCES.md` for full provenance.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set TABPFN_TOKEN

PYTHONPATH=. uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Regenerate training CSV from Open-Meteo:

```bash
python scripts/fetch_real_data.py
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/weather?lat=&lon=` | Today's real conditions (Open-Meteo) |
| `GET` | `/api/health` | Engine + data source status |
| `POST` | `/api/check` | TabPFN prediction + checklist |

## Prize categories

- **Best Use of TabPFN**
- **Best Use of Render**

## License

MIT
