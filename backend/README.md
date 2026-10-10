# Evidence Radar — Backend

FastAPI service for Evidence Radar + Trials. **Hour-1 mode serves hardcoded mocks** so the frontend can build before live Open Targets / ClinicalTrials.gov fetch.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY later; not needed for mocks
```

## Run (mock API)

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Open docs: http://127.0.0.1:8000/docs

## Endpoints

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | Liveness |
| GET | `/genes?disease=asthma` | Quadrant points |
| GET | `/genes/{id}` | Detail + score breakdown |
| GET | `/genes/{id}/trials` | Trial timeline |
| GET | `/genes/{id}/judgment` | Judgment card |
| GET | `/genes/{id}/robustness` | Rank stability |
| GET | `/events` | Change feed (mock events labeled `simulated`) |

Gene ids are Ensembl IDs (e.g. `ENSG00000134352`) or symbols (e.g. `IL6R`).

## Contract notes

- Scores are **evidence strength, not recommendations**.
- Judgment field `for` is serialized as JSON key `for` (Pydantic alias).
- Gemini key stays in `.env` only; never in the frontend.
- Next: `fetch_all.py` → cache under `/data/raw` → replace mocks.

## Disease config

See `config.json` (asthma / `EFO_0000270`). Confirm the ID in Open Targets before live pull.
