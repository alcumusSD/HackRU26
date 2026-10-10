"""Parse CT.gov studies, join to genes, recompute activity scores."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.drug_gene_map import genes_for_intervention
from app.models import Gene, ScoreBreakdownItem, Trial
from app.parse_genes import _clamp01, assign_quadrant


PHASE_SCORE = {
    "EARLY_PHASE1": 0.2,
    "PHASE1": 0.25,
    "PHASE1/PHASE2": 0.4,
    "PHASE2": 0.5,
    "PHASE2/PHASE3": 0.65,
    "PHASE3": 0.75,
    "PHASE4": 1.0,
}


def _module(study: Dict[str, Any], name: str) -> Dict[str, Any]:
    return ((study.get("protocolSection") or {}).get(name)) or {}


def flatten_study(study: Dict[str, Any]) -> Dict[str, Any]:
    ident = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    design = _module(study, "designModule")
    arms = _module(study, "armsInterventionsModule")
    conditions = _module(study, "conditionsModule")

    interventions = []
    for item in arms.get("interventions") or []:
        name = item.get("name")
        if name:
            interventions.append(
                {
                    "name": name,
                    "type": item.get("type"),
                }
            )

    phases = design.get("phases") or []
    start = (status.get("startDateStruct") or {}).get("date")
    end = (status.get("completionDateStruct") or {}).get("date")

    return {
        "nct_id": ident.get("nctId"),
        "brief_title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "phases": phases,
        "phase": phases[0] if phases else "NA",
        "start_date": start,
        "end_date": end,
        "why_stopped": status.get("whyStopped"),
        "interventions": interventions,
        "conditions": conditions.get("conditions") or [],
    }


def link_study_to_genes(
    flat: Dict[str, Any], demo_symbols: Set[str]
) -> Set[str]:
    hits: Set[str] = set()
    for intervention in flat.get("interventions") or []:
        hits |= genes_for_intervention(intervention.get("name") or "", demo_symbols)
    title = flat.get("brief_title") or ""
    hits |= genes_for_intervention(title, demo_symbols)
    return hits


def to_api_trial(
    flat: Dict[str, Any],
    gene_symbols: List[str],
    *,
    classify_stops: bool = False,
    use_gemini: bool = False,
) -> Trial:
    skip_drugs = {"placebo", "none", "none (observational study)", "n/a"}
    drugs = []
    for i in flat.get("interventions") or []:
        name = (i.get("name") or "").strip()
        if not name or name.lower() in skip_drugs:
            continue
        drugs.append(name)

    why = flat.get("why_stopped")
    category = flat.get("stop_reason_category")
    quote = flat.get("stop_reason_quote") or why
    verified = bool(flat.get("quote_verified"))

    # Classify on the fly if not already attached to the flat study.
    status = (flat.get("status") or "").upper()
    stopped = status in {"TERMINATED", "WITHDRAWN", "SUSPENDED"}
    if classify_stops and stopped and why and not category:
        from app.gemini_client import classify_stop_reason
        from app.models import StopReasonCategory

        classified = classify_stop_reason(why, use_gemini=use_gemini)
        category = classified.category
        if classified.quote:
            quote = classified.quote
        verified = bool(classified.quote_verified)
        if isinstance(category, StopReasonCategory):
            category = category

    if isinstance(category, str):
        from app.models import StopReasonCategory

        try:
            category = StopReasonCategory(category)
        except ValueError:
            category = StopReasonCategory.OTHER

    return Trial(
        nct_id=flat["nct_id"],
        phase=flat.get("phase") or "NA",
        status=flat.get("status") or "UNKNOWN",
        drugs=drugs,
        target_genes=gene_symbols,
        stop_reason_category=category,
        stop_reason_quote=quote,
        quote_verified=verified,
        start_date=flat.get("start_date"),
        end_date=flat.get("end_date"),
    )


def _started_recent(start_date: Optional[str], years: int = 5) -> bool:
    if not start_date:
        return False
    try:
        year = int(str(start_date)[:4])
    except ValueError:
        return False
    return year >= datetime.now(timezone.utc).year - years


def furthest_phase_score(trials: List[Dict[str, Any]]) -> float:
    best = 0.0
    for t in trials:
        for phase in t.get("phases") or [t.get("phase")]:
            if not phase:
                continue
            best = max(best, PHASE_SCORE.get(str(phase).upper(), 0.0))
    return best


def activity_from_trials(
    trials: List[Dict[str, Any]], volume_cap: int = 20
) -> Tuple[float, List[ScoreBreakdownItem], bool]:
    """Return activity score 0-1, breakdown items, safety_flag."""
    n = len(trials)
    if n == 0:
        return (
            0.0,
            [
                ScoreBreakdownItem(
                    component="trial_volume",
                    value=0.0,
                    weight=0.30,
                    sources=["ClinicalTrials.gov"],
                ),
                ScoreBreakdownItem(
                    component="furthest_phase",
                    value=0.0,
                    weight=0.40,
                    sources=["ClinicalTrials.gov"],
                ),
                ScoreBreakdownItem(
                    component="recency",
                    value=0.0,
                    weight=0.30,
                    sources=["ClinicalTrials.gov"],
                ),
            ],
            False,
        )

    volume = math.log1p(n) / math.log1p(volume_cap)
    volume = _clamp01(volume)
    phase = _clamp01(furthest_phase_score(trials))
    recent = sum(1 for t in trials if _started_recent(t.get("start_date"))) / n
    recent = _clamp01(recent)

    score = 0.30 * volume + 0.40 * phase + 0.30 * recent

    # Light track-record adjustments when stop categories are already present.
    futility_n = sum(
        1 for t in trials if (t.get("stop_reason_category") or "") == "futility"
    )
    if futility_n:
        score = _clamp01(score - 0.05 * min(futility_n, 3))

    safety = any(
        (t.get("stop_reason_category") or "") == "safety"
        or "safety" in (t.get("why_stopped") or "").lower()
        for t in trials
    )

    breakdown = [
        ScoreBreakdownItem(
            component="trial_volume",
            value=volume,
            weight=0.30,
            sources=[f"ClinicalTrials.gov (n={n})"],
        ),
        ScoreBreakdownItem(
            component="furthest_phase",
            value=phase,
            weight=0.40,
            sources=["ClinicalTrials.gov"],
        ),
        ScoreBreakdownItem(
            component="recency",
            value=recent,
            weight=0.30,
            sources=["ClinicalTrials.gov (share started ≤5y)"],
        ),
    ]
    return _clamp01(score), breakdown, safety


def parse_and_join_trials(
    raw_trials: Dict[str, Any],
    genes: List[Gene],
    genetic_cut: float = 0.5,
    activity_cut: float = 0.5,
    *,
    classify_stops: bool = False,
    use_gemini: bool = False,
) -> Tuple[List[Gene], Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """Enrich genes with CT.gov activity; return trials_by_gene_id and summary."""
    demo_symbols = {g.symbol for g in genes}

    studies = raw_trials.get("studies") or []
    flats: List[Dict[str, Any]] = []
    for study in studies:
        flat = flatten_study(study)
        if not flat.get("nct_id"):
            continue
        linked = link_study_to_genes(flat, demo_symbols)
        flat["linked_genes"] = sorted(linked)
        flats.append(flat)

    if classify_stops:
        from app.gemini_client import classify_stop_reason

        for flat in flats:
            status = (flat.get("status") or "").upper()
            why = (flat.get("why_stopped") or "").strip()
            if status not in {"TERMINATED", "WITHDRAWN", "SUSPENDED"} or not why:
                continue
            classified = classify_stop_reason(why, use_gemini=use_gemini)
            if classified.category is not None:
                flat["stop_reason_category"] = classified.category.value
            if classified.quote:
                flat["stop_reason_quote"] = classified.quote
            flat["quote_verified"] = bool(classified.quote_verified)

    trials_by_symbol: Dict[str, List[Dict[str, Any]]] = {s: [] for s in demo_symbols}
    mapped = 0
    for flat in flats:
        if flat["linked_genes"]:
            mapped += 1
        for symbol in flat["linked_genes"]:
            trials_by_symbol[symbol].append(flat)

    enriched: List[Gene] = []
    trials_by_gene_id: Dict[str, List[Dict[str, Any]]] = {}

    for gene in genes:
        gene_trials = trials_by_symbol.get(gene.symbol, [])
        activity, trial_breakdown, safety = activity_from_trials(gene_trials)

        # Keep OT genetic breakdown; append trial activity components.
        keep = [
            b
            for b in gene.score_breakdown
            if b.component
            not in {"trial_volume", "furthest_phase", "recency", "clinical"}
        ]
        # Retain OT clinical as reference component (not used for axis anymore).
        for b in gene.score_breakdown:
            if b.component == "clinical":
                keep.append(
                    ScoreBreakdownItem(
                        component="open_targets_clinical_ref",
                        value=b.value,
                        weight=0.0,
                        sources=["Open Targets clinical (reference only)"],
                    )
                )
        keep.extend(trial_breakdown)

        new_gene = gene.model_copy(
            update={
                "activity_score": activity,
                "score_breakdown": keep,
                "quadrant": assign_quadrant(
                    gene.genetic_score, activity, genetic_cut, activity_cut
                ),
                "partial_data": len(gene_trials) == 0,
                "safety_flag": safety,
            }
        )
        enriched.append(new_gene)

        api_trials = [
            to_api_trial(
                t,
                t.get("linked_genes") or [gene.symbol],
                classify_stops=classify_stops,
                use_gemini=use_gemini,
            ).model_dump(mode="json")
            for t in gene_trials
        ]
        # Stable sort: phase depth then start date
        api_trials.sort(key=lambda t: (t.get("phase") or "", t.get("start_date") or ""))
        trials_by_gene_id[gene.id] = api_trials

    classified_n = sum(
        1
        for trials in trials_by_gene_id.values()
        for t in trials
        if t.get("stop_reason_category")
    )
    verified_n = sum(
        1
        for trials in trials_by_gene_id.values()
        for t in trials
        if t.get("quote_verified")
    )

    notes = (
        "activity_score from ClinicalTrials.gov volume/phase/recency; "
        "drug→gene join uses curated synonym map + symbol mentions"
    )
    if classify_stops:
        notes += (
            f"; stop reasons classified ({classified_n} categorized, "
            f"{verified_n} quotes verified"
            f"{'; Gemini' if use_gemini else '; heuristic'})"
        )
        notes += "; light futility penalty applied when category=futility"
    else:
        notes += "; stop-reason classification skipped (pass --classify-stops)"

    summary = {
        "studies_fetched": len(studies),
        "studies_flattened": len(flats),
        "studies_mapped_to_demo_genes": mapped,
        "genes_with_trials": sum(1 for g in enriched if not g.partial_data),
        "genes_without_trials": sum(1 for g in enriched if g.partial_data),
        "stop_reasons_classified": classified_n,
        "stop_quotes_verified": verified_n,
        "classify_stops": classify_stops,
        "classify_engine": (
            ("gemini+heuristic" if use_gemini else "heuristic")
            if classify_stops
            else "none"
        ),
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }
    return enriched, trials_by_gene_id, summary
