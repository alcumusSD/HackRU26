#!/usr/bin/env python3
"""Fetch Open Targets associations for one disease (small scale) and parse to API genes.

Usage:
  python fetch_all.py           # skip if raw cache exists
  python fetch_all.py --force   # refetch and re-parse

Writes:
  data/raw/genes.json
  data/processed/genes.json
  data/validation_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from app.open_targets import fetch_disease_targets  # noqa: E402
from app.parse_genes import genes_to_jsonable, parse_open_targets_payload  # noqa: E402

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
CONFIG_PATH = BACKEND / "config.json"
RAW_GENES = DATA_RAW / "genes.json"
PROCESSED_GENES = DATA_PROCESSED / "genes.json"
VALIDATION = ROOT / "data" / "validation_report.md"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"wrote: {path.relative_to(ROOT)}")


def write_validation(summary: dict, genes_count: int) -> None:
    lines = [
        "# Validation report (Open Targets small-scale)",
        "",
        f"- Parsed at: `{summary.get('parsed_at')}`",
        f"- Disease: `{summary.get('disease_name')}` (`{summary.get('disease_id')}`)",
        f"- Open Targets association count: {summary.get('ot_association_count')}",
        f"- Genes parsed for demo: {genes_count}",
        f"- Skipped rows: {summary.get('skipped_rows')}",
        f"- Genes missing clinical datatype (partial activity): {summary.get('partial_activity_count')}",
        "",
        "## Notes",
        "",
        f"- {summary.get('notes')}",
        "- Trials and judgment cards still use mock/default paths.",
        "- ClinicalTrials.gov join is not wired yet.",
        "",
    ]
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.write_text("\n".join(lines))
    print(f"wrote: {VALIDATION.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Open Targets disease targets")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refetch even if data/raw/genes.json exists",
    )
    args = parser.parse_args()

    config = load_config()
    disease = config.get("disease", {})
    disease_id = disease.get("efo_id") or "MONDO_0004979"
    limit = int(config.get("gene_limit", 15))
    url = (config.get("open_targets") or {}).get(
        "graphql_url",
        "https://api.platform.opentargets.org/api/v4/graphql",
    )
    cuts = config.get("quadrant_cutoff") or {}
    genetic_cut = float(cuts.get("genetic", 0.5))
    activity_cut = float(cuts.get("activity", 0.5))

    stamp = datetime.now(timezone.utc).isoformat()

    if RAW_GENES.exists() and not args.force:
        print(f"skip fetch (exists): {RAW_GENES.relative_to(ROOT)} — use --force to refetch")
        raw = json.loads(RAW_GENES.read_text())
    else:
        print(f"fetching Open Targets: disease={disease_id} limit={limit}")
        body = fetch_disease_targets(disease_id=disease_id, limit=limit, url=url)
        raw = {
            "fetched_at": stamp,
            "query": {
                "source": "open_targets_graphql",
                "url": url,
                "disease_id": disease_id,
                "limit": limit,
            },
            "response": body,
        }
        write_json(RAW_GENES, raw)

    # Support both wrapped and bare GraphQL bodies
    gql = raw.get("response") if isinstance(raw.get("response"), dict) else raw
    genes, summary = parse_open_targets_payload(
        gql, genetic_cut=genetic_cut, activity_cut=activity_cut
    )
    if not genes:
        print("ERROR: no genes parsed", file=sys.stderr)
        return 1

    processed = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "disease": {
            "id": summary.get("disease_id"),
            "name": summary.get("disease_name"),
        },
        "source": "open_targets",
        "gene_count": len(genes),
        "summary": summary,
        "genes": genes_to_jsonable(genes),
    }
    write_json(PROCESSED_GENES, processed)
    write_validation(summary, len(genes))

    # Refresh data_as_of in config for the API footer
    config["data_as_of"] = stamp[:10]
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    print(f"updated: {CONFIG_PATH.relative_to(ROOT)} data_as_of={config['data_as_of']}")
    print(f"OK: {len(genes)} genes ready. Set DATA_MODE=cached (or auto) and restart API.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
