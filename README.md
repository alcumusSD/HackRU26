# Evidence Radar + Trials

Interactive evidence map: genetic support × clinical trial activity, plus a **judgment layer** (for / against / missing / could-change-if / robustness). Built for HackRU; roles and full plan in [partner-roles.md](partner-roles.md).

## Status

- **Backend:** FastAPI with mock **or** Open Targets cached genes (`DATA_MODE=auto`)
- **Frontend:** interactive Evidence × Activity map + judgment panel
- **Live fetch:** Open Targets asthma (top 15) wired; ClinicalTrials.gov / Gemini not yet

## Quick start

```bash
# Terminal 1 — API (+ optional Open Targets pull)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python fetch_all.py --force    # once: cache asthma genes from Open Targets
uvicorn app.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend
npm install
npm run dev
```

- API: http://127.0.0.1:8000/genes?disease=asthma  
- UI: http://localhost:3000

## Layout

```
backend/          FastAPI + Pydantic contract + mocks
data/raw/         Cached API pulls (later)
data/processed/   Joined tables (later)
data/snapshots/   Change-feed snapshots (later)
frontend/         Next.js map UI
```

## Design rules

1. Gemini reads text only; **our code scores**.
2. Every AI claim needs a **verified source quote**.
3. Demo path uses **cached data** — no live APIs on stage.
4. Credit Open Targets and other public sources on screen.
