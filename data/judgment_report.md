# Judgment implementation report

**Date:** 2026-10-10  
**Status:** Shipped (cached mode)

## What changed

Judgment cards are no longer mock narrative in `DATA_MODE=cached`. They are assembled from Open Targets gene scores + ClinicalTrials.gov linked trials, with classified `whyStopped` quotes.

| Layer | File(s) | Role |
|---|---|---|
| Quote check | `backend/app/quote_verify.py` | Quote must appear in source (normalized / fuzzy) |
| Classifier | `backend/app/gemini_client.py` | `classify_stop_reason` — heuristic default, Gemini optional, disk cache |
| Parse wire | `backend/app/parse_trials.py` | Classify stopped studies before activity join |
| Fetch flags | `backend/fetch_all.py` | `--reparse-trials`, `--classify-stops`, `--gemini-stops` |
| Assembler | `backend/app/judgment.py` | For / Against / Missing / could-change-if / robustness |
| API path | `backend/app/data_store.py` | Cached → `assemble_judgment`; mock fixtures unchanged |
| UI | `JudgmentPanel.tsx`, `globals.css` | Against + trial stop quotes |

## Pipeline

1. Flatten CT.gov studies → link drugs/titles to demo genes  
2. For TERMINATED / WITHDRAWN / SUSPENDED with `whyStopped`: classify → category + excerpt + `quote_verified`  
3. Recompute activity (light futility penalty when category=`futility`)  
4. On `/genes/{id}/judgment`: build card from gene + trials + peer reweight  

## Rebuild command used

```bash
python fetch_all.py --reparse-trials --classify-stops
```

Engine this run: **heuristic** (no Gemini API calls). Cache dir: `data/cache/gemini/`.

## Validation snapshot

| Metric | Value |
|---|---|
| Studies fetched | 298 |
| Mapped to demo genes | 173 |
| Genes with trials | 12 / 15 |
| Stopped studies | 19 |
| Categorized | 17 |
| Quotes verified | 17 |
| Categories | low_enrollment 7 · business 5 · other 3 · futility 1 · safety 1 · none 2 |

### Sample: IL5

- Linked trials: 48  
- Against items: 4 (terminated/withdrawn with stop text + verified quotes)  
- Includes business, low_enrollment, futility (“didn’t meet primary endpoint”), other  
- Card confidence: high  
- Robustness: stable (peer evidence×activity reweight)

### Sample: TSLP / IL4R

- Against empty when no stopped studies carry whyStopped text (expected)

## Honesty notes

| Field | Real? | Notes |
|---|---|---|
| Genetic / activity scores | Yes | OT + CT.gov |
| Against quotes | Yes | From CT.gov `whyStopped`, verified in source |
| Stop category | Yes (heuristic) | Gemini available via `--gemini-stops` |
| For items | Code-assembled | From scores/trial counts, not LLM prose |
| Robustness | Lightweight | Deterministic 200-run reweight across peers — not full Monte Carlo |
| Missing / could-change-if | Heuristic rules | Transparent gap flags |

## How to verify in UI

1. Restart backend so it reloads processed JSON  
2. Open a gene with stopped trials (e.g. **IL5**)  
3. Judgment panel → Against should show NCT + category + quote · “quote verified”  
4. Linked trials list shows stop category and italic quote when present  

## Remaining (not this slice)

- Commit (exclude `.env`)  
- Optional Gemini reclassify pass  
- Change-feed / timeline polish  
