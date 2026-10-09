# PLOT

**Leave the screen. Tend the ground.**

PLOT is a Hacktoberfest Week 1 (*Touch Grass*) project. It uses **Prior Labs TabPFN** — an open tabular foundation model — to classify today’s outdoor action as **wait**, **walk**, or **garden** from frost and weather features. Then it returns a short checklist meant to end at your door, not in a chat thread.

## Live demo

- **App:** https://plot-touch-grass.onrender.com
- **Repo:** https://github.com/PranjalManhgaye/plot-touch-grass

Hosted on **Render** (free tier). First request after idle may take ~30s while the service wakes up and TabPFN fits.

## Why TabPFN

Garden and frost decisions are **tables**, not prose. TabPFN is built for that: fit on historical outdoor rows, predict a class for today’s row. No closed garden API. You can swap models, keep location data local to your machine, and run the same CSV offline.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. Create a key at https://platform.priorlabs.ai
# 2. Copy env and set the token
cp .env.example .env

PYTHONPATH=. uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Without `TABPFN_TOKEN`, the API loads a **clearly labeled** local `HistGradientBoosting` baseline so the UI still works. The UI and `/api/health` never claim that baseline is TabPFN.

## Deploy on Render

1. Connect this repo as a **Web Service** (Python).
2. Build: `pip install -r requirements.txt`
3. Start: `PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Health check: `/api/healthz`
5. Add secret env var `TABPFN_TOKEN` (never commit it).

Or use the Blueprint in `render.yaml` from the Render dashboard → New → Blueprint.

Free instances spin down after idle; the first request may take a few seconds while TabPFN fits.

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/healthz` | Liveness |
| `GET` | `/api/health` | Engine status (`tabpfn` or `baseline`) |
| `GET` | `/api/presets` | Example places |
| `POST` | `/api/check` | Predict action + outdoor checklist |

## Project layout

```
plot/
  data/outdoor_history.csv   # training table
  backend/engine.py          # TabPFN (+ transparent baseline)
  backend/checklist.py       # wait / walk / garden tasks
  backend/main.py            # FastAPI
  web/                       # static UI
  render.yaml                # Render Blueprint
```

## Prize categories

- **Best Use of TabPFN** (primary)
- **Best Use of Render** (hosting)
- Optional: Entire / Sentry if you attach agent sessions and traces in the DEV write-up

## License

MIT
