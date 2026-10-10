# Evidence Radar + Trials

Interactive evidence map: genetic support × clinical trial activity, plus a **judgment layer** (for / against / missing / could-change-if / robustness). Built for HackRU; roles and full plan in [partner-roles.md](partner-roles.md).

## Status

- **Backend:** mock FastAPI API (Person A hour-1 handoff)
- **Frontend:** not scaffolded yet (Person B)
- **Live fetch:** not started — use mocks first

## Quick start (API)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Try: http://127.0.0.1:8000/genes?disease=asthma

## Layout

```
backend/          FastAPI + Pydantic contract + mocks
data/raw/         Cached API pulls (later)
data/processed/   Joined tables (later)
data/snapshots/   Change-feed snapshots (later)
frontend/         Next.js UI (Person B)
```

## Design rules

1. Gemini reads text only; **our code scores**.
2. Every AI claim needs a **verified source quote**.
3. Demo path uses **cached data** — no live APIs on stage.
4. Credit Open Targets and other public sources on screen.
