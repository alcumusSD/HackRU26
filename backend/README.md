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

## Fetch data (asthma, small scale)

```bash
cd backend
source .venv/bin/activate
python fetch_all.py                 # skip existing raw caches
python fetch_all.py --force         # refetch OT + CT.gov
python fetch_all.py --force-trials  # refetch trials only
```

Writes:

- `data/raw/genes.json` — Open Targets GraphQL
- `data/raw/trials.json` — ClinicalTrials.gov studies
- `data/processed/genes.json` — UI-shaped genes (activity from trials)
- `data/processed/trials_by_gene.json` — trials per gene
- `data/validation_report.md`

Disease ID: **`MONDO_0004979`**.  
`genetic_score` from Open Targets; `activity_score` from CT.gov volume/phase/recency (curated drug→gene map). Judgment still mock/default.

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
| GET | `/health` | `mode` + `gemini` |
| GET | `/gemini/ping` | Live Gemini smoke test |
| POST | `/chat` | Grounded Q&A over UI context snapshot |
| GET | `/genes?disease=asthma` | Quadrant points |
| GET | `/genes/{id}` | Detail + score breakdown |
| GET | `/genes/{id}/trials` | CT.gov trials when cached |
| GET | `/genes/{id}/judgment` | Mock/default judgment |
| GET | `/genes/{id}/robustness` | From judgment |
| GET | `/events` | Mock change feed (`simulated`) |
| GET | `/network?disease=asthma` | Gene–drug network for the Network tab |

## Contract notes

- Scores are **evidence strength, not recommendations**.
- Judgment field `for` serializes as JSON key `for`.
- Gemini key stays in `.env` only.
- Frontend keeps the same shapes — only gene scores/source change in cached mode.
