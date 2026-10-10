#!/usr/bin/env python3
"""Fetch Open Targets + ClinicalTrials.gov (per disease, small scale) and build API payloads.

Usage:
  python fetch_all.py --disease asthma
  python fetch_all.py --disease copd --force
  python fetch_all.py --force              # refetch default disease
  python fetch_all.py --force-trials       # refetch trials only
  python fetch_all.py --skip-trials        # Open Targets genes only
  python fetch_all.py --reparse-trials     # rebuild processed from raw (no refetch)
  python fetch_all.py --reparse-trials --classify-stops
  python fetch_all.py --reparse-trials --classify-stops --gemini-stops

Writes:
  data/raw/<slug>/genes.json
  data/raw/<slug>/trials.json
  data/processed/<slug>/genes.json
  data/processed/<slug>/trials_by_gene.json
  data/validation_report.md
"""

from __future__ import annotations

import argparse
import json
import shutil
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
VALIDATION = ROOT / "data" / "validation_report.md"

# Legacy flat layout (pre multi-disease)
LEGACY_RAW_GENES = DATA_RAW / "genes.json"
LEGACY_RAW_TRIALS = DATA_RAW / "trials.json"
LEGACY_PROCESSED_GENES = DATA_PROCESSED / "genes.json"
LEGACY_PROCESSED_TRIALS = DATA_PROCESSED / "trials_by_gene.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def migrate_legacy_asthma_cache() -> None:
    """Move flat asthma files into data/*/asthma/ once."""
    pairs = [
        (LEGACY_RAW_GENES, DATA_RAW / "asthma" / "genes.json"),
        (LEGACY_RAW_TRIALS, DATA_RAW / "asthma" / "trials.json"),
        (LEGACY_PROCESSED_GENES, DATA_PROCESSED / "asthma" / "genes.json"),
        (LEGACY_PROCESSED_TRIALS, DATA_PROCESSED / "asthma" / "trials_by_gene.json"),
    ]
    moved = False
    for src, dest in pairs:
        if src.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            print(f"migrated: {src.relative_to(ROOT)} → {dest.relative_to(ROOT)}")
            moved = True
        elif src.exists() and dest.exists():
            src.unlink()
            print(f"removed legacy duplicate: {src.relative_to(ROOT)}")
            moved = True
    if not moved and any(p[0].exists() for p in pairs):
        pass


def disease_paths(slug: str) -> dict[str, Path]:
    return {
        "raw_genes": DATA_RAW / slug / "genes.json",
        "raw_trials": DATA_RAW / slug / "trials.json",
        "processed_genes": DATA_PROCESSED / slug / "genes.json",
        "processed_trials": DATA_PROCESSED / slug / "trials_by_gene.json",
    }


def resolve_disease_entry(config: dict, slug: str) -> tuple[str, dict]:
    diseases = config.get("diseases") or {}
    if diseases:
        if slug not in diseases:
            known = ", ".join(sorted(diseases)) or "(none)"
            raise SystemExit(f"Unknown disease '{slug}'. Known: {known}")
        return slug, diseases[slug]

    # Back-compat: single disease object
    disease = config.get("disease") or {}
    name = (disease.get("name") or "asthma").lower()
    if slug not in {name, "asthma"} and slug != name:
        raise SystemExit(f"Unknown disease '{slug}' (legacy config only has {name})")
    return name, disease


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"wrote: {path.relative_to(ROOT)}")


def write_validation(ot_summary, trial_summary, genes_count: int, slug: str) -> None:
    lines = [
        "# Validation report",
        "",
        f"## Disease: `{slug}`",
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
            f"- Stop reasons classified: {trial_summary.get('stop_reasons_classified', 0)}",
            f"- Stop quotes verified: {trial_summary.get('stop_quotes_verified', 0)}",
            f"- Classify engine: {trial_summary.get('classify_engine', 'none')}",
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
        "## Judgment",
        "",
        "- Cards assembled live from gene scores + linked trials (`app/judgment.py`)",
        "- Against items use verified whyStopped quotes when classified",
        "- Robustness = deterministic reweight of evidence×activity across peers",
        "",
        "## Still deferred",
        "",
        "- Change-feed events",
        "- Full Monte-Carlo robustness (current is lightweight reweight)",
        "",
    ]
    VALIDATION.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION.write_text("\n".join(lines))
    print(f"wrote: {VALIDATION.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Open Targets + ClinicalTrials.gov for a configured disease"
    )
    parser.add_argument(
        "--disease",
        default=None,
        help="Disease slug from config (default: default_disease)",
    )
    parser.add_argument("--force", action="store_true", help="Refetch all raw sources")
    parser.add_argument(
        "--force-trials", action="store_true", help="Refetch trials even if cached"
    )
    parser.add_argument(
        "--skip-trials", action="store_true", help="Only refresh Open Targets genes"
    )
    parser.add_argument(
        "--reparse-trials",
        action="store_true",
        help="Rebuild processed genes/trials from existing raw (no CT.gov refetch)",
    )
    parser.add_argument(
        "--classify-stops",
        action="store_true",
        help="Classify TERMINATED/WITHDRAWN/SUSPENDED whyStopped texts",
    )
    parser.add_argument(
        "--gemini-stops",
        action="store_true",
        help="Use Gemini for stop classification (else heuristic; requires --classify-stops)",
    )
    args = parser.parse_args()

    if args.gemini_stops and not args.classify_stops:
        print("ERROR: --gemini-stops requires --classify-stops", file=sys.stderr)
        return 2

    migrate_legacy_asthma_cache()

    config = load_config()
    slug = args.disease or config.get("default_disease") or "asthma"
    slug, disease = resolve_disease_entry(config, slug)
    paths = disease_paths(slug)

    disease_id = disease.get("efo_id") or "MONDO_0004979"
    disease_name = disease.get("name") or slug
    limit = int(config.get("gene_limit", 15))
    ot_url = (config.get("open_targets") or {}).get(
        "graphql_url",
        "https://api.platform.opentargets.org/api/v4/graphql",
    )
    ct_cfg = config.get("clinicaltrials") or {}
    max_studies = int(ct_cfg.get("max_studies", 150))
    extra_drugs = disease.get("extra_interventions") or ct_cfg.get(
        "extra_interventions"
    ) or [
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

    raw_genes_path = paths["raw_genes"]
    raw_trials_path = paths["raw_trials"]
    processed_genes_path = paths["processed_genes"]
    processed_trials_path = paths["processed_trials"]

    # --- Open Targets ---
    if raw_genes_path.exists() and not args.force:
        print(f"skip OT fetch (exists): {raw_genes_path.relative_to(ROOT)}")
        raw_genes = json.loads(raw_genes_path.read_text())
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
        write_json(raw_genes_path, raw_genes)

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
        need_trials = (
            args.force
            or args.force_trials
            or not raw_trials_path.exists()
        )
        if args.reparse_trials and raw_trials_path.exists():
            need_trials = False

        if not need_trials and raw_trials_path.exists():
            print(f"skip CT.gov fetch (exists): {raw_trials_path.relative_to(ROOT)}")
            raw_trials = json.loads(raw_trials_path.read_text())
        elif need_trials:
            print(
                f"fetching ClinicalTrials.gov: cond={disease_name} max={max_studies}"
            )
            payload = fetch_studies(
                condition=disease_name,
                max_studies=max_studies,
                extra_interventions=list(extra_drugs),
            )
            raw_trials = {"fetched_at": stamp, **payload}
            write_json(raw_trials_path, raw_trials)
        else:
            print("ERROR: no raw trials; run without --skip-trials first", file=sys.stderr)
            return 1

        if args.classify_stops:
            engine = "gemini+heuristic" if args.gemini_stops else "heuristic"
            print(f"classifying stop reasons ({engine})…")

        genes, trials_by_gene, trial_summary = parse_and_join_trials(
            raw_trials,
            genes,
            genetic_cut=genetic_cut,
            activity_cut=activity_cut,
            classify_stops=args.classify_stops,
            use_gemini=args.gemini_stops,
        )
        write_json(
            processed_trials_path,
            {
                "built_at": datetime.now(timezone.utc).isoformat(),
                "disease": disease_name,
                "slug": slug,
                "summary": trial_summary,
                "trials_by_gene": trials_by_gene,
            },
        )

    processed = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "disease": {
            "id": ot_summary.get("disease_id"),
            "name": ot_summary.get("disease_name"),
            "slug": slug,
        },
        "source": "open_targets+clinicaltrials"
        if trial_summary
        else "open_targets",
        "gene_count": len(genes),
        "summary": {"open_targets": ot_summary, "clinicaltrials": trial_summary},
        "genes": genes_to_jsonable(genes),
    }
    write_json(processed_genes_path, processed)
    write_validation(ot_summary, trial_summary, len(genes), slug)

    config["data_as_of"] = stamp[:10]
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    print(f"updated: config data_as_of={config['data_as_of']}")
    print(f"OK: {len(genes)} genes ready for disease={slug} (mode=auto/cached).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
