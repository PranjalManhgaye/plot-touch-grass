# PLOT

**Leave the screen. Tend the ground.**

PLOT is a Hacktoberfest Week 1 (*Touch Grass*) project. It uses **Prior Labs TabPFN** — an open tabular foundation model — to classify today’s outdoor action as **wait**, **walk**, or **garden** from frost and weather features. Then it returns a short checklist meant to end at your door, not in a chat thread.

## Why TabPFN

Garden and frost decisions are **tables**, not prose. TabPFN is built for that: fit on historical outdoor rows, predict a class for today’s row. No closed garden API. You can swap models, keep location data local to your machine, and run the same CSV offline.

## Quick start

```bash
cd plot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For the real TabPFN demo (recommended for submission):
# 1. Create a key at https://platform.priorlabs.ai
# 2. cp .env.example .env  and set TABPFN_TOKEN=...

cp .env.example .env
PYTHONPATH=. uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Without `TABPFN_TOKEN`, the API loads a **clearly labeled** local `HistGradientBoosting` baseline so the UI still works. The UI and `/api/health` never claim that baseline is TabPFN.

## API

| Method | Path | Purpose |
|--------|------|---------|
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
```

## Prize categories

- **Best Use of TabPFN** (primary)
- Optional: Entire / Sentry if you attach agent sessions and traces in the DEV write-up

## License

MIT — see `LICENSE` if present; otherwise treat as MIT for Hacktoberfest sharing.
