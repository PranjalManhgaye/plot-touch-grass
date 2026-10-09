*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built

**PLOT** tells you whether to **wait**, **walk**, or **garden** today — then gives a three-step checklist that ends at the door.

It is not a chatbot. The brain is **TabPFN** (Prior Labs), an open tabular foundation model, fitted on frost and weather history. The UI’s job is short: enter conditions → get a signal → go outside.

Who it’s for: people with a yard, balcony, or nearby park who overthink the weather and under-leave the house.

## Demo

**Live:** https://plot-touch-grass.onrender.com

Local: `PYTHONPATH=. uvicorn backend.main:app` → http://127.0.0.1:8000

<!-- Add a 45s outdoor video/GIF after you use it outside -->

## Code

https://github.com/PranjalManhgaye/plot-touch-grass

## How I Built It

1. Built a historical outdoor table (`data/outdoor_history.csv`) with frost lag, temps, rain, wind, daylight, soil moisture.
2. Fitted **TabPFNClassifier** (`tabpfn-client`) when `TABPFN_TOKEN` is set; transparently falls back to a labeled sklearn baseline only for local UI testing — never claimed as TabPFN.
3. Mapped the predicted class to a concrete outdoor checklist (screen stays under a minute).
4. Shipped a single-purpose FastAPI + static UI — brand first, one CTA, no chat chrome.

## Why Does Open Innovation Matter?

Frost and “should I plant?” are **tabular** problems. A closed garden API would lock location and weather to a vendor. TabPFN lets me:

- Keep the frost table and inference path under my control
- Swap models without rewriting the product
- Run a meaningful demo without paying per chat token
- Explain the decision as class probabilities over real features — not opaque prose

Open tabular models fit outdoor logistics better than a general chat API.

## My Agent Session

<!-- Optional: DevRelay / Entire embed -->

## Prize Categories

- Best Use of TabPFN
- Best Use of Render
- Best Use of Entire *(if agent session embedded)*
- Best Use of Sentry Agent Tracing *(if traces added)*
