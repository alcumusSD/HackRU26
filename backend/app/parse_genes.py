"""Parse Open Targets raw associations into API Gene models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.models import Gene, Quadrant, ScoreBreakdownItem
from app.open_targets import datatype_score


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def assign_quadrant(
    genetic: float,
    activity: float,
    genetic_cut: float = 0.5,
    activity_cut: float = 0.5,
) -> Quadrant:
    high_g = genetic >= genetic_cut
    high_a = activity >= activity_cut
    if high_g and high_a:
        return Quadrant.VALIDATED
    if high_g and not high_a:
        return Quadrant.WHITE_SPACE
    if not high_g and high_a:
        return Quadrant.CAUTION
    return Quadrant.DEPRIORITIZE


def row_to_gene(
    row: Dict[str, Any],
    genetic_cut: float = 0.5,
    activity_cut: float = 0.5,
) -> Gene:
    target = row.get("target") or {}
    gene_id = target.get("id")
    symbol = target.get("approvedSymbol")
    if not gene_id or not symbol:
        raise ValueError("Association row missing target id or symbol")

    overall = _clamp01(float(row.get("score") or 0.0))
    genetic = datatype_score(row, "genetic_association")
    clinical = datatype_score(row, "clinical")

    genetic_score = _clamp01(genetic if genetic is not None else overall)
    # Until ClinicalTrials.gov is wired, use OT clinical datatype as activity proxy.
    activity_score = _clamp01(clinical if clinical is not None else 0.0)
    partial = clinical is None

    breakdown: List[ScoreBreakdownItem] = [
        ScoreBreakdownItem(
            component="open_targets_overall",
            value=overall,
            weight=0.0,
            sources=["Open Targets associatedTargets.score"],
        )
    ]
    for item in row.get("datatypeScores") or []:
        if item.get("score") is None:
            continue
        breakdown.append(
            ScoreBreakdownItem(
                component=str(item["id"]),
                value=_clamp01(float(item["score"])),
                weight=0.0,
                sources=["Open Targets datatypeScores"],
            )
        )

    return Gene(
        id=gene_id,
        symbol=symbol,
        genetic_score=genetic_score,
        activity_score=activity_score,
        score_breakdown=breakdown,
        protective_variant=False,
        quadrant=assign_quadrant(
            genetic_score, activity_score, genetic_cut, activity_cut
        ),
        contradictions=[],
        partial_data=partial,
        safety_flag=False,
    )


def parse_open_targets_payload(
    raw: Dict[str, Any],
    genetic_cut: float = 0.5,
    activity_cut: float = 0.5,
) -> Tuple[List[Gene], Dict[str, Any]]:
    """Return genes + a small validation summary."""
    disease = (raw.get("data") or {}).get("disease") or {}
    rows = ((disease.get("associatedTargets") or {}).get("rows")) or []

    genes: List[Gene] = []
    skipped = 0
    for row in rows:
        try:
            genes.append(row_to_gene(row, genetic_cut, activity_cut))
        except (TypeError, ValueError, KeyError):
            skipped += 1

    summary = {
        "disease_id": disease.get("id"),
        "disease_name": disease.get("name"),
        "ot_association_count": (disease.get("associatedTargets") or {}).get("count"),
        "parsed_genes": len(genes),
        "skipped_rows": skipped,
        "partial_activity_count": sum(1 for g in genes if g.partial_data),
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "activity_score uses Open Targets 'clinical' datatype as a proxy; "
            "genetic_score uses genetic_association when present else overall score."
        ),
    }
    return genes, summary


def genes_to_jsonable(genes: List[Gene]) -> List[Dict[str, Any]]:
    return [g.model_dump(mode="json") for g in genes]
