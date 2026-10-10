# Validation report

## Disease: `asthma`

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
- Stop reasons classified: 0
- Stop quotes verified: 0
- Classify engine: none
- Notes: activity_score from ClinicalTrials.gov volume/phase/recency; drug→gene join uses curated synonym map + symbol mentions; stop-reason classification skipped (pass --classify-stops)

## Judgment

- Cards assembled live from gene scores + linked trials (`app/judgment.py`)
- Against items use verified whyStopped quotes when classified
- Robustness = deterministic reweight of evidence×activity across peers

## Still deferred

- Change-feed events
- Full Monte-Carlo robustness (current is lightweight reweight)
