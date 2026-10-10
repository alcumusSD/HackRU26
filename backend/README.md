# Evidence Radar — Backend

FastAPI service for Evidence Radar + Trials.

**Data modes** (`DATA_MODE` in `.env`):

| Mode | Genes | Judgment / trials |
|------|--------|-------------------|
| `auto` (default) | Open Targets processed file if present, else mocks | Mock / default cards |
| `cached` | `data/processed/genes.json` | Mock / default cards |
| `mock` | Hardcoded mocks | Mocks |

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Fetch Open Targets (asthma, top 15)

```bash
cd backend
source .venv/bin/activate
python fetch_all.py          # skip if raw cache exists
python fetch_all.py --force  # refetch
```

Writes:

- `data/raw/genes.json` — raw GraphQL response
- `data/processed/genes.json` — UI-shaped genes
- `data/validation_report.md`

Disease ID: **`MONDO_0004979`** (asthma in current Open Targets).  
`activity_score` currently uses the Open Targets **clinical** datatype as a proxy until ClinicalTrials.gov is wired.

## Run API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

- Docs: http://127.0.0.1:8000/docs  
- Health mode field shows `cached` or `mock`

## Endpoints

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | Includes `mode` |
| GET | `/genes?disease=asthma` | Quadrant points |
| GET | `/genes/{id}` | Detail + score breakdown |
| GET | `/genes/{id}/trials` | Mock trials when available |
| GET | `/genes/{id}/judgment` | Mock/default judgment |
| GET | `/genes/{id}/robustness` | From judgment |
| GET | `/events` | Mock change feed (`simulated`) |

## Contract notes

- Scores are **evidence strength, not recommendations**.
- Judgment field `for` serializes as JSON key `for`.
- Gemini key stays in `.env` only.
- Frontend keeps the same shapes — only gene scores/source change in cached mode.
