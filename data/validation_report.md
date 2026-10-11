# Validation report

## Disease: `alz`

## Open Targets

- Disease: `Alzheimer disease` (`MONDO_0004975`)
- Association count in OT: 13006
- Genes parsed: 15
- Skipped OT rows: 0

## ClinicalTrials.gov

- Studies fetched: 261
- Studies mapped to demo genes: 146
- Genes with ≥1 linked trial: 8
- Genes with no linked trial (partial_data): 7
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
