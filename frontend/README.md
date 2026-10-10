# Evidence Radar — Frontend

Interactive Evidence × Activity map for asthma genes. Talks to the FastAPI mock backend.

## Setup

```bash
# Terminal 1 — API
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — UI
cd frontend
cp .env.local.example .env.local   # if needed
npm install
npm run dev
```

Open http://localhost:3000

## What you get

- Full-viewport quadrant map (genetic evidence vs trial activity)
- Shape + color legend (color-blind friendly)
- Click a gene → judgment panel (For / Against / Missing / Could-change-if)
- Cached-data footer and “not a recommendation” disclaimer
