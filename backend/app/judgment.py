"""Assemble real judgment cards from gene scores + linked trials.

Gemini is used only for stop-reason classification (via trials already
classified). Card structure, confidence, missing gaps, and could-change-if
are code-owned.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Sequence

from app.models import (
    AgainstItem,
    CardConfidence,
    ConfidenceBand,
    CouldChangeIf,
    EnrollmentRisk,
    EvidenceItem,
    Gene,
    JudgmentCard,
    Robustness,
    StopReasonCategory,
    Trial,
)


def _confidence(gene: Gene) -> ConfidenceBand:
    if gene.genetic_score >= 0.75:
        return ConfidenceBand.STRONG
    if gene.genetic_score >= 0.45:
        return ConfidenceBand.MODERATE
    return ConfidenceBand.THIN


def _robustness(gene: Gene, peers: Sequence[Gene]) -> Robustness:
    """Lightweight rank-stability estimate across peer genes (not mock narrative)."""
    if not peers:
        peers = [gene]
    runs = 200
    top_k = min(5, max(1, len(peers)))
    # Deterministic pseudo-reweights of evidence/activity mix
    hits = 0
    for i in range(runs):
        w_g = 0.35 + (i % 7) * 0.05  # 0.35..0.65
        w_a = 1.0 - w_g
        ranked = sorted(
            peers,
            key=lambda g: -(w_g * g.genetic_score + w_a * g.activity_score),
        )
        top_ids = {g.id for g in ranked[:top_k]}
        if gene.id in top_ids:
            hits += 1
    share = hits / runs
    label: Literal["stable", "moderate", "fragile"]
    if share >= 0.7:
        label = "stable"
    elif share >= 0.4:
        label = "moderate"
    else:
        label = "fragile"
    return Robustness(
        top_k=top_k,
        runs=runs,
        share_in_top_k=round(share, 3),
        label=label,
    )


def _for_items(gene: Gene, trials: List[Trial], data_as_of: str) -> List[EvidenceItem]:
    items: List[EvidenceItem] = [
        EvidenceItem(
            text=(
                f"{gene.symbol} genetic association score "
                f"{gene.genetic_score:.2f} from Open Targets."
            ),
            source="Open Targets",
            date=data_as_of,
            evidence_type="database",
        )
    ]
    n = len(trials)
    if n:
        phases = sorted({t.phase for t in trials if t.phase and t.phase != "NA"})
        phase_note = f" furthest phase among linked trials: {phases[-1]}." if phases else ""
        items.append(
            EvidenceItem(
                text=(
                    f"{n} linked ClinicalTrials.gov studies"
                    f" (activity score {gene.activity_score:.2f}).{phase_note}"
                ),
                source="ClinicalTrials.gov",
                date=data_as_of,
                evidence_type="trial",
            )
        )
    if gene.quadrant.value == "validated":
        items.append(
            EvidenceItem(
                text="Quadrant Validated: strong genetics with substantial trial activity.",
                source="Evidence Radar scoring",
                date=data_as_of,
                evidence_type="database",
            )
        )
    return items


def _against_items(gene: Gene, trials: List[Trial]) -> List[AgainstItem]:
    against: List[AgainstItem] = []
    for t in trials:
        status = (t.status or "").upper()
        if status not in {"TERMINATED", "WITHDRAWN", "SUSPENDED"}:
            continue
        quote = (t.stop_reason_quote or "").strip()
        if not quote:
            continue
        cat = t.stop_reason_category
        verified = bool(t.quote_verified)
        kind: Literal["failed_trial", "contradiction", "safety", "stale"]
        if cat == StopReasonCategory.SAFETY:
            kind = "safety"
        else:
            kind = "failed_trial"
        label = cat.value.replace("_", " ") if cat else "unclassified stop"
        against.append(
            AgainstItem(
                id=t.nct_id,
                text=f"{t.nct_id} {status.lower()} ({label}).",
                quote=quote[:280],
                quote_verified=verified,
                source=f"ClinicalTrials.gov:{t.nct_id}",
                kind=kind,
            )
        )
    # Cap for UI readability
    return against[:8]


def _missing(gene: Gene, trials: List[Trial]) -> List[str]:
    missing: List[str] = []
    if gene.partial_data or not trials:
        missing.append("no_linked_trials")
    phases = {(t.phase or "").upper() for t in trials}
    late = any(p.startswith("PHASE2") or p.startswith("PHASE3") or p == "PHASE4" for p in phases)
    if trials and not late:
        missing.append("no_phase2_plus_results")
    stopped = [
        t
        for t in trials
        if (t.status or "").upper() in {"TERMINATED", "WITHDRAWN", "SUSPENDED"}
    ]
    if stopped and not any(t.stop_reason_quote for t in stopped):
        missing.append("missing_why_stopped_text")
    if gene.genetic_score < 0.45:
        missing.append("thin_genetic_evidence")
    return missing


def _could_change_if(gene: Gene, trials: List[Trial]) -> List[CouldChangeIf]:
    items = [
        CouldChangeIf(
            event="new_trial_status_change",
            effect="activity score and quadrant may move",
        )
    ]
    if any(
        (t.status or "").upper() in {"RECRUITING", "ACTIVE_NOT_RECRUITING"}
        for t in trials
    ):
        items.append(
            CouldChangeIf(
                event="recruiting_trial_completes_or_terminates",
                effect="activity/recency components and Against list may update",
            )
        )
    if gene.genetic_score >= 0.6 and gene.activity_score < 0.4:
        items.append(
            CouldChangeIf(
                event="first_industry_sponsored_phase2",
                effect="could exit white_space into validated or caution",
            )
        )
    return items


def _open_questions(gene: Gene, missing: List[str], against: List[AgainstItem]) -> List[str]:
    qs: List[str] = []
    if "no_linked_trials" in missing:
        qs.append(f"Why are no ClinicalTrials.gov interventions linked to {gene.symbol} yet?")
    if "no_phase2_plus_results" in missing:
        qs.append(f"Is there Phase 2+ evidence for {gene.symbol} outside this join map?")
    if against:
        qs.append(
            f"Do terminated studies against {gene.symbol} reflect target failure or trial design?"
        )
    if not qs:
        qs.append(
            f"What additional human evidence would most change confidence in {gene.symbol}?"
        )
    return qs[:3]


def _card_confidence(
    gene: Gene,
    against: List[AgainstItem],
    missing: List[str],
) -> CardConfidence:
    verified = sum(1 for a in against if a.quote_verified)
    if gene.partial_data or len(missing) >= 2:
        return CardConfidence.LOW
    if against and verified < len(against):
        return CardConfidence.MODERATE
    if gene.genetic_score >= 0.6 and (against == [] or verified == len(against)):
        return CardConfidence.HIGH
    return CardConfidence.MODERATE


def _is_low_enrollment_stop(trial: Trial) -> bool:
    status = (trial.status or "").upper()
    if status not in {"TERMINATED", "WITHDRAWN", "SUSPENDED"}:
        return False
    if trial.stop_reason_category == StopReasonCategory.LOW_ENROLLMENT:
        return True
    blob = (trial.stop_reason_quote or "").lower()
    return any(
        k in blob
        for k in ("enroll", "recruit", "accrual", "slow enrollment")
    )


def _enrollment_risk(gene: Gene, trials: List[Trial]) -> EnrollmentRisk:
    """Plain-language enrollment risk from linked CT.gov trials."""
    n = len(trials)
    if n == 0:
        return EnrollmentRisk(
            level="unknown",
            linked_trials=0,
            summary=(
                f"No linked trials for {gene.symbol} yet — enrollment risk "
                "cannot be estimated from this cache."
            ),
        )

    low_enroll = [t for t in trials if _is_low_enrollment_stop(t)]
    recruiting = [
        t for t in trials if (t.status or "").upper() == "RECRUITING"
    ]
    active = [
        t
        for t in trials
        if (t.status or "").upper() == "ACTIVE_NOT_RECRUITING"
    ]
    stopped_n = len(low_enroll)
    recruiting_n = len(recruiting)
    active_n = len(active)
    samples = [t.nct_id for t in low_enroll[:4]]

    level: Literal["low", "moderate", "high", "unknown"]
    if stopped_n >= 2 or (stopped_n >= 1 and recruiting_n >= 2):
        level = "high"
        summary = (
            f"High enrollment-risk pattern for {gene.symbol}: "
            f"{stopped_n} linked "
            f"{'study' if stopped_n == 1 else 'studies'} stopped with "
            f"enrollment/recruitment language"
            + (
                f", and {recruiting_n} still recruiting"
                if recruiting_n
                else ""
            )
            + ". Expect harder patient accrual unless the plan differs clearly."
        )
    elif stopped_n == 1:
        level = "moderate"
        summary = (
            f"Moderate enrollment risk for {gene.symbol}: "
            f"1 linked study stopped citing enrollment/recruitment"
            + (
                f"; {recruiting_n} currently recruiting"
                if recruiting_n
                else ""
            )
            + ". Review that stop reason before locking a protocol."
        )
    else:
        level = "low"
        summary = (
            f"No low-enrollment stops among {n} linked "
            f"{'trial' if n == 1 else 'trials'} for {gene.symbol}"
            + (
                f"; {recruiting_n} currently recruiting"
                if recruiting_n
                else ""
            )
            + ". Enrollment risk looks lower in this cache — still not a forecast."
        )

    return EnrollmentRisk(
        level=level,
        linked_trials=n,
        stopped_low_enrollment=stopped_n,
        recruiting=recruiting_n,
        active_not_recruiting=active_n,
        summary=summary,
        sample_ncts=samples,
    )


def assemble_judgment(
    gene: Gene,
    trials: List[Trial],
    *,
    data_as_of: str,
    peers: Optional[Sequence[Gene]] = None,
) -> JudgmentCard:
    """Build a judgment card from real gene + trial fields."""
    peer_list = list(peers) if peers is not None else [gene]
    against = _against_items(gene, trials)
    missing = _missing(gene, trials)
    return JudgmentCard(
        gene_id=gene.id,
        confidence=_confidence(gene),
        robustness=_robustness(gene, peer_list),
        for_=_for_items(gene, trials, data_as_of),
        against=against,
        missing=missing,
        could_change_if=_could_change_if(gene, trials),
        conflicts=[],
        open_questions=_open_questions(gene, missing, against),
        data_as_of=data_as_of,
        card_confidence=_card_confidence(gene, against, missing),
        enrollment_risk=_enrollment_risk(gene, trials),
    )
