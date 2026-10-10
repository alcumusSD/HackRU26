#!/usr/bin/env python3
"""Fetch Open Targets + ClinicalTrials.gov (asthma, small scale) and build API payloads.

Usage:
  python fetch_all.py              # skip existing raw caches
  python fetch_all.py --force      # refetch everything
  python fetch_all.py --force-trials   # refetch trials only
  python fetch_all.py --skip-trials    # Open Targets genes only

Writes:
  data/raw/genes.json
  data/raw/trials.json
  data/processed/genes.json
  data/processed/trials_by_gene.json
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

from app.clinicaltrials import fetch_studies  # noqa: E402
from app.open_targets import fetch_disease_targets  # noqa: E402
from app.parse_genes import genes_to_jsonable, parse_open_targets_payload  # noqa: E402
from app.parse_trials import parse_and_join_trials  # noqa: E402

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
CONFIG_PATH = BACKEND / "config.json"
RAW_GENES = DATA_RAW / "genes.json"
RAW_TRIALS = DATA_RAW / "trials.json"
PROCESSED_GENES = DATA_PROCESSED / "genes.json"
PROCESSED_TRIALS = DATA_PROCESSED / "trials_by_gene.json"
VALIDATION = ROOT / "data" / "validation_report.md"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"wrote: {path.relative_to(ROOT)}")


def write_validation(ot_summary, trial_summary, genes_count: int) -> None:
    lines = [
        "# Validation report",
        "",
        "## Open Targets",
        "",
        f"- Disease: `{ot_summary.get('disease_name')}` (`{ot_summary.get('disease_id')}`)",
        f"- Association count in OT: {ot_summary.get('ot_association_count')}",
        f"- Genes parsed: {genes_count}",
        f"- Skipped OT rows: {ot_summary.get('skipped_rows')}",
        "",
    ]
    if trial_summary:
        lines += [
            "## ClinicalTrials.gov",
            "",
            f"- Studies fetched: {trial_summary.get('studies_fetched')}",
            f"- Studies mapped to demo genes: {trial_summary.get('studies_mapped_to_demo_genes')}",
            f"- Genes with ≥1 linked trial: {trial_summary.get('genes_with_trials')}",
            f"- Genes with no linked trial (partial_data): {trial_summary.get('genes_without_trials')}",
            f"- Notes: {trial_summary.get('notes')}",
            "",
        ]
    else:
        lines += [
            "## ClinicalTrials.gov",
            "",
            "- Skipped this run.",
            "",
        ]
    lines += [
        "## Still mock / deferred",
        "",
        "- Judgment cards (Gemini + quote verify)",
        "- Stop-reason categories / futility track-record adjustment",
        "- Change-feed events",
        "",
    ]
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.write_text("\n".join(lines))
    print(f"wrote: {VALIDATION.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Open Targets + ClinicalTrials.gov for asthma demo"
    )
    parser.add_argument("--force", action="store_true", help="Refetch all raw sources")
    parser.add_argument(
        "--force-trials", action="store_true", help="Refetch trials even if cached"
    )
    parser.add_argument(
        "--skip-trials", action="store_true", help="Only refresh Open Targets genes"
    )
    args = parser.parse_args()

    config = load_config()
    disease = config.get("disease", {})
    disease_id = disease.get("efo_id") or "MONDO_0004979"
    disease_name = disease.get("name") or "asthma"
    limit = int(config.get("gene_limit", 15))
    ot_url = (config.get("open_targets") or {}).get(
        "graphql_url",
        "https://api.platform.opentargets.org/api/v4/graphql",
    )
    ct_cfg = config.get("clinicaltrials") or {}
    max_studies = int(ct_cfg.get("max_studies", 150))
    extra_drugs = ct_cfg.get("extra_interventions") or [
        "dupilumab",
        "tezepelumab",
        "mepolizumab",
        "benralizumab",
        "omalizumab",
        "montelukast",
        "roflumilast",
    ]
    cuts = config.get("quadrant_cutoff") or {}
    genetic_cut = float(cuts.get("genetic", 0.5))
    activity_cut = float(cuts.get("activity", 0.5))
    stamp = datetime.now(timezone.utc).isoformat()

    # --- Open Targets ---
    if RAW_GENES.exists() and not args.force:
        print(f"skip OT fetch (exists): {RAW_GENES.relative_to(ROOT)}")
        raw_genes = json.loads(RAW_GENES.read_text())
    else:
        print(f"fetching Open Targets: disease={disease_id} limit={limit}")
        body = fetch_disease_targets(disease_id=disease_id, limit=limit, url=ot_url)
        raw_genes = {
            "fetched_at": stamp,
            "query": {
                "source": "open_targets_graphql",
                "url": ot_url,
                "disease_id": disease_id,
                "limit": limit,
            },
            "response": body,
        }
        write_json(RAW_GENES, raw_genes)

    gql = raw_genes.get("response") if isinstance(raw_genes.get("response"), dict) else raw_genes
    genes, ot_summary = parse_open_targets_payload(
        gql, genetic_cut=genetic_cut, activity_cut=activity_cut
    )
    if not genes:
        print("ERROR: no genes parsed", file=sys.stderr)
        return 1

    trial_summary = None
    trials_by_gene: dict = {}

    # --- ClinicalTrials.gov ---
    if not args.skip_trials:
        need_trials = args.force or args.force_trials or not RAW_TRIALS.exists()
        if not need_trials:
            print(f"skip CT.gov fetch (exists): {RAW_TRIALS.relative_to(ROOT)}")
            raw_trials = json.loads(RAW_TRIALS.read_text())
        else:
            print(
                f"fetching ClinicalTrials.gov: cond={disease_name} max={max_studies}"
            )
            payload = fetch_studies(
                condition=disease_name,
                max_studies=max_studies,
                extra_interventions=list(extra_drugs),
            )
            raw_trials = {"fetched_at": stamp, **payload}
            write_json(RAW_TRIALS, raw_trials)

        genes, trials_by_gene, trial_summary = parse_and_join_trials(
            raw_trials,
            genes,
            genetic_cut=genetic_cut,
            activity_cut=activity_cut,
        )
        write_json(
            PROCESSED_TRIALS,
            {
                "built_at": datetime.now(timezone.utc).isoformat(),
                "disease": disease_name,
                "summary": trial_summary,
                "trials_by_gene": trials_by_gene,
            },
        )

    processed = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "disease": {
            "id": ot_summary.get("disease_id"),
            "name": ot_summary.get("disease_name"),
        },
        "source": "open_targets+clinicaltrials"
        if trial_summary
        else "open_targets",
        "gene_count": len(genes),
        "summary": {"open_targets": ot_summary, "clinicaltrials": trial_summary},
        "genes": genes_to_jsonable(genes),
    }
    write_json(PROCESSED_GENES, processed)
    write_validation(ot_summary, trial_summary, len(genes))

    config["data_as_of"] = stamp[:10]
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    print(f"updated: config data_as_of={config['data_as_of']}")
    print(f"OK: {len(genes)} genes ready (mode=auto/cached).")
    return 0


if __name__ == "__main__":
    # Python 3.9 compatibility for dict | None in write_validation annotation
    sys.exit(main())
