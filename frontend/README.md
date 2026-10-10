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

- **Map** tab — Evidence × Activity quadrant (default for demos)
- **Network** tab — 3D force graph of **gene–drug** links from trials (different data than the score map); orbit/zoom/click
- Shape + color legend (color-blind friendly)
- Click a gene → judgment panel + clickable ClinicalTrials.gov links
- Cached-data footer and “not a recommendation” disclaimer
