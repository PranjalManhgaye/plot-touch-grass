*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

**PLOT** answers one question: should you **wait**, **walk**, or **garden** today?

It is not a chatbot. Pick a city or share your location — **Open-Meteo** fills in today's real weather. **TabPFN** (Prior Labs) classifies your day from 30k+ rows of **real ERA5 reanalysis** (2018–2024, 12 US cities). You get three concrete outdoor steps. The screen's job is under a minute.

Who it's for: anyone with a yard, balcony, or nearby park who stares at the weather app instead of going outside.

## Demo

**Live:** https://plot-touch-grass.onrender.com

<!-- Add 45s video: pick city → live weather loads → garden signal → you outside -->

## Code

https://github.com/PranjalManhgaye/plot-touch-grass

## How I Built It

1. **Real training data** — `scripts/fetch_real_data.py` pulls daily ERA5 weather from Open-Meteo for Portland, Seattle, Chicago, Minneapolis, Denver, NYC, Boston, Atlanta, Austin, Phoenix, Miami, LA (2018–2024). ~30,684 rows. No synthetic temperatures.
2. **Frost features** — `days_since_last_frost` computed from actual daily min temps crossing 0 °C. Soil moisture from Open-Meteo hourly probes.
3. **Labels** — horticulture-inspired heuristics in `backend/labels.py` (frost window, precip, wind). Honest and documented — TabPFN learns the table, not prose.
4. **TabPFN** — `tabpfn-client` fits on real rows; predicts wait/walk/garden with class probabilities.
5. **Live weather** — `/api/weather` uses Open-Meteo forecast + 120-day archive. UI: city presets, geolocation, refresh.
6. **Deployed** on Render with a clean static UI — brand first, one CTA.

## Why Does Open Innovation Matter?

Frost and planting decisions are **tabular**. A closed garden API would lock your coordinates and history to a vendor.

Open stack wins here:

- **Open-Meteo** — free ERA5 data, no key, works on the trail with cached tables
- **TabPFN** — swap models, explain decisions as probabilities over real features
- **Your data stays yours** — we don't store location; weather is fetched per request

Closed chat APIs can't beat a tabular foundation model on structured frost history — and they shouldn't pretend to.

## My Agent Session

<!-- Optional: DevRelay / Entire embed -->

## Prize Categories

- Best Use of TabPFN
- Best Use of Render
