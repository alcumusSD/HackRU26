# Validation report

## Open Targets

- Disease: `asthma` (`MONDO_0004979`)
- Association count in OT: 7772
- Genes parsed: 15
- Skipped OT rows: 0

## ClinicalTrials.gov

- Studies fetched: 298
- Studies mapped to demo genes: 173
- Genes with ≥1 linked trial: 12
- Genes with no linked trial (partial_data): 3
- Notes: activity_score from ClinicalTrials.gov volume/phase/recency; drug→gene join uses curated synonym map + symbol mentions; futility track-record adjustment deferred until Gemini classifier.

## Still mock / deferred

- Judgment cards (Gemini + quote verify)
- Stop-reason categories / futility track-record adjustment
- Change-feed events
