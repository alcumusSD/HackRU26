#!/usr/bin/env python3
"""Idempotent data pull skeleton (Person A, hours 1–8).

Fetches public sources into ../data/raw/. Skips files that already exist.
Live Open Targets / ClinicalTrials.gov calls are not wired yet — run the mock API for UI work.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def write_if_missing(path: Path, payload: dict) -> None:
    if path.exists():
        print(f"skip (exists): {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"wrote: {path.relative_to(ROOT)}")


def main() -> int:
    config = load_config()
    stamp = datetime.now(timezone.utc).isoformat()
    disease = config.get("disease", {})

    # Placeholders only — replace with real API clients next.
    write_if_missing(
        DATA_RAW / "genes.json",
        {
            "fetched_at": stamp,
            "query": {"source": "open_targets", "disease": disease},
            "status": "placeholder",
            "items": [],
        },
    )
    write_if_missing(
        DATA_RAW / "drugs.json",
        {
            "fetched_at": stamp,
            "query": {"source": "open_targets_or_chembl", "disease": disease},
            "status": "placeholder",
            "items": [],
        },
    )
    write_if_missing(
        DATA_RAW / "trials.json",
        {
            "fetched_at": stamp,
            "query": {"source": "clinicaltrials_gov_v2", "disease": disease},
            "status": "placeholder",
            "items": [],
        },
    )
    write_if_missing(
        DATA_RAW / "genetics.json",
        {
            "fetched_at": stamp,
            "query": {"source": "gwas_catalog_gnomad", "disease": disease},
            "status": "placeholder",
            "items": [],
        },
    )
    print("Done. Wire real fetchers before relying on data/raw for scoring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
