"""Hardcoded mock responses so Person B can build before live fetch."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from app.models import (
    AgainstItem,
    CardConfidence,
    ConfidenceBand,
    Conflict,
    CouldChangeIf,
    Event,
    EvidenceItem,
    Gene,
    JudgmentCard,
    Quadrant,
    Robustness,
    ScoreBreakdownItem,
    StopReasonCategory,
    Trial,
)

DATA_AS_OF = "2026-10-10"
DISEASE = "asthma"

GENES: List[Gene] = [
    Gene(
        id="ENSG00000027697",
        symbol="IL4R",
        genetic_score=0.86,
        activity_score=0.78,
        protective_variant=True,
        quadrant=Quadrant.VALIDATED,
        score_breakdown=[
            ScoreBreakdownItem(
                component="gwas_association",
                value=0.88,
                weight=0.55,
                sources=["Open Targets genetic association"],
            ),
            ScoreBreakdownItem(
                component="protective_variant",
                value=1.0,
                weight=0.30,
                sources=["GWAS Catalog"],
            ),
            ScoreBreakdownItem(
                component="independent_evidence_types",
                value=0.66,
                weight=0.15,
                sources=["GWAS", "rare variant"],
            ),
        ],
    ),
    Gene(
        id="ENSG00000169194",
        symbol="IL13",
        genetic_score=0.81,
        activity_score=0.72,
        protective_variant=False,
        quadrant=Quadrant.VALIDATED,
        score_breakdown=[
            ScoreBreakdownItem(
                component="gwas_association",
                value=0.84,
                weight=0.55,
                sources=["Open Targets genetic association"],
            ),
            ScoreBreakdownItem(
                component="protective_variant",
                value=0.5,
                weight=0.30,
                sources=["direction unclear"],
            ),
            ScoreBreakdownItem(
                component="independent_evidence_types",
                value=0.66,
                weight=0.15,
                sources=["GWAS", "drug"],
            ),
        ],
    ),
    Gene(
        id="ENSG00000134352",
        symbol="IL6R",
        genetic_score=0.74,
        activity_score=0.22,
        protective_variant=True,
        quadrant=Quadrant.WHITE_SPACE,
        score_breakdown=[
            ScoreBreakdownItem(
                component="gwas_association",
                value=0.76,
                weight=0.55,
                sources=["Open Targets genetic association"],
            ),
            ScoreBreakdownItem(
                component="protective_variant",
                value=1.0,
                weight=0.30,
                sources=["GWAS Catalog"],
            ),
            ScoreBreakdownItem(
                component="independent_evidence_types",
                value=0.33,
                weight=0.15,
                sources=["GWAS"],
            ),
        ],
        contradictions=["against_1"],
    ),
    Gene(
        id="ENSG00000169031",
        symbol="COL6A5",
        genetic_score=0.68,
        activity_score=0.18,
        protective_variant=False,
        quadrant=Quadrant.WHITE_SPACE,
        score_breakdown=[
            ScoreBreakdownItem(
                component="gwas_association",
                value=0.70,
                weight=0.55,
                sources=["Open Targets genetic association"],
            ),
            ScoreBreakdownItem(
                component="protective_variant",
                value=0.5,
                weight=0.30,
                sources=["unclear"],
            ),
            ScoreBreakdownItem(
                component="independent_evidence_types",
                value=0.33,
                weight=0.15,
                sources=["GWAS"],
            ),
        ],
    ),
    Gene(
        id="ENSG00000105371",
        symbol="ICAM1",
        genetic_score=0.28,
        activity_score=0.65,
        protective_variant=False,
        quadrant=Quadrant.CAUTION,
        score_breakdown=[
            ScoreBreakdownItem(
                component="gwas_association",
                value=0.25,
                weight=0.55,
                sources=["Open Targets genetic association"],
            ),
            ScoreBreakdownItem(
                component="protective_variant",
                value=0.5,
                weight=0.30,
                sources=["unclear"],
            ),
            ScoreBreakdownItem(
                component="independent_evidence_types",
                value=0.33,
                weight=0.15,
                sources=["trial"],
            ),
        ],
        safety_flag=True,
    ),
    Gene(
        id="ENSG00000142208",
        symbol="AKT1",
        genetic_score=0.22,
        activity_score=0.15,
        protective_variant=False,
        quadrant=Quadrant.DEPRIORITIZE,
        score_breakdown=[
            ScoreBreakdownItem(
                component="gwas_association",
                value=0.20,
                weight=0.55,
                sources=["Open Targets genetic association"],
            ),
            ScoreBreakdownItem(
                component="protective_variant",
                value=0.5,
                weight=0.30,
                sources=["unclear"],
            ),
            ScoreBreakdownItem(
                component="independent_evidence_types",
                value=0.33,
                weight=0.15,
                sources=["database"],
            ),
        ],
        partial_data=True,
    ),
]

TRIALS_BY_GENE: Dict[str, List[Trial]] = {
    "ENSG00000027697": [
        Trial(
            nct_id="NCT01234567",
            phase="Phase 3",
            status="Completed",
            drugs=["dupilumab"],
            target_genes=["IL4R"],
            start_date="2013-01-01",
            end_date="2017-06-01",
        ),
        Trial(
            nct_id="NCT07654321",
            phase="Phase 2",
            status="Terminated",
            drugs=["example-il4r-mab"],
            target_genes=["IL4R"],
            stop_reason_category=StopReasonCategory.LOW_ENROLLMENT,
            stop_reason_quote="Study terminated due to slow enrollment.",
            quote_verified=True,
            start_date="2019-03-01",
            end_date="2021-01-15",
        ),
    ],
    "ENSG00000134352": [
        Trial(
            nct_id="NCT09876543",
            phase="Phase 1",
            status="Terminated",
            drugs=["example-il6r-asset"],
            target_genes=["IL6R"],
            stop_reason_category=StopReasonCategory.LOW_ENROLLMENT,
            stop_reason_quote="Insufficient enrollment to continue.",
            quote_verified=True,
            start_date="2020-05-01",
            end_date="2021-08-01",
        ),
        Trial(
            nct_id="NCT05551234",
            phase="Phase 2",
            status="Terminated",
            drugs=["example-il6r-asset-2"],
            target_genes=["IL6R"],
            stop_reason_category=StopReasonCategory.FUTILITY,
            stop_reason_quote="Terminated for futility based on interim analysis.",
            quote_verified=True,
            start_date="2018-02-01",
            end_date="2020-11-01",
        ),
    ],
    "ENSG00000105371": [
        Trial(
            nct_id="NCT04445566",
            phase="Phase 2",
            status="Terminated",
            drugs=["example-icam1"],
            target_genes=["ICAM1"],
            stop_reason_category=StopReasonCategory.SAFETY,
            stop_reason_quote="Study stopped after safety review board recommendation.",
            quote_verified=True,
            start_date="2016-04-01",
            end_date="2018-09-01",
        ),
    ],
}

JUDGMENT_BY_GENE: Dict[str, JudgmentCard] = {
    "ENSG00000027697": JudgmentCard(
        gene_id="ENSG00000027697",
        confidence=ConfidenceBand.STRONG,
        robustness=Robustness(
            top_k=5,
            runs=1000,
            share_in_top_k=0.91,
            label="stable",
            rank_p5=1,
            rank_p95=4,
        ),
        for_=[
            EvidenceItem(
                text="Strong genetic association with asthma and protective-variant signal consistent with blocking IL4R.",
                source="Open Targets / GWAS Catalog",
                date="2024-06-01",
                evidence_type="gwas",
            ),
            EvidenceItem(
                text="Multiple completed late-phase programs targeting this pathway.",
                source="ClinicalTrials.gov",
                date="2023-01-01",
                evidence_type="trial",
            ),
        ],
        against=[
            AgainstItem(
                id="against_il4r_1",
                text="One Phase 2 asset stopped for low enrollment; this does not lower the activity score.",
                quote="Study terminated due to slow enrollment.",
                quote_verified=True,
                source="NCT07654321",
                kind="failed_trial",
            )
        ],
        missing=["limited_non_european_ancestry_coverage"],
        could_change_if=[
            CouldChangeIf(
                event="large_safety_signal_in_postmarket",
                effect="safety flag raised; quadrant unchanged unless efficacy evidence weakens",
            )
        ],
        conflicts=[],
        open_questions=[
            "How consistent is the protective effect across ancestry groups?",
            "Would a new futility stop in a related pathway asset change confidence?",
        ],
        data_as_of=DATA_AS_OF,
        card_confidence=CardConfidence.HIGH,
    ),
    "ENSG00000134352": JudgmentCard(
        gene_id="ENSG00000134352",
        confidence=ConfidenceBand.MODERATE,
        robustness=Robustness(
            top_k=5,
            runs=1000,
            share_in_top_k=0.42,
            label="fragile",
            rank_p5=3,
            rank_p95=18,
        ),
        for_=[
            EvidenceItem(
                text="Protective genetic signal with direction consistent with inhibition.",
                source="GWAS Catalog",
                date="2022-09-01",
                evidence_type="gwas",
            )
        ],
        against=[
            AgainstItem(
                id="against_1",
                text="A Phase 2 program reported futility at interim analysis.",
                quote="Terminated for futility based on interim analysis.",
                quote_verified=True,
                source="NCT05551234",
                kind="failed_trial",
            ),
            AgainstItem(
                id="against_2",
                text="Genetic evidence is concentrated in European-ancestry studies.",
                quote="Primary association reported in European ancestry meta-analysis.",
                quote_verified=True,
                source="GWAS Catalog (mock)",
                kind="stale",
            ),
        ],
        missing=["no_completed_phase2_success", "single_ancestry_group"],
        could_change_if=[
            CouldChangeIf(
                event="futility_stop_another_phase2",
                effect="activity score drops further; may leave white_space toward caution",
            ),
            CouldChangeIf(
                event="failed_replication_of_top_gwas",
                effect="genetic score falls; quadrant may become deprioritize",
            ),
        ],
        conflicts=[
            Conflict(
                claim_a="Genetics supports IL6R as an asthma-relevant target.",
                claim_b="A clinical program stopped for futility in this disease area.",
                difference="method",
            )
        ],
        open_questions=[
            "Was the futility stop disease-specific or asset-specific?",
            "Is there an independent replication outside European ancestry?",
            "What Phase 2 design would most efficiently resolve the gap?",
        ],
        data_as_of=DATA_AS_OF,
        card_confidence=CardConfidence.MODERATE,
    ),
}

# Default judgment for genes without a custom card
def default_judgment(gene: Gene) -> JudgmentCard:
    if gene.genetic_score >= 0.7 and gene.activity_score >= 0.5:
        label: Literal["stable", "moderate", "fragile"] = "stable"
        share = 0.85
    elif gene.genetic_score >= 0.6:
        label = "fragile"
        share = 0.35
    else:
        label = "moderate"
        share = 0.60
    return JudgmentCard(
        gene_id=gene.id,
        confidence=(
            ConfidenceBand.STRONG
            if gene.genetic_score >= 0.75
            else ConfidenceBand.MODERATE
            if gene.genetic_score >= 0.45
            else ConfidenceBand.THIN
        ),
        robustness=Robustness(
            top_k=5,
            runs=1000,
            share_in_top_k=share,
            label=label,
        ),
        for_=[
            EvidenceItem(
                text=f"Mock genetic association for {gene.symbol}.",
                source="Open Targets (mock)",
                date=DATA_AS_OF,
                evidence_type="database",
            )
        ],
        against=[],
        missing=["no_phase2_results"] if gene.activity_score < 0.4 else [],
        could_change_if=[
            CouldChangeIf(
                event="new_trial_status_change",
                effect="activity score and quadrant may move",
            )
        ],
        conflicts=[],
        open_questions=[
            f"What additional evidence would most change confidence in {gene.symbol}?",
        ],
        data_as_of=DATA_AS_OF,
        card_confidence=CardConfidence.LOW,
    )


EVENTS: List[Event] = [
    Event(
        gene="IL6R",
        what_changed="Trial NCT05551234 status changed to Terminated (futility)",
        before=0.34,
        after=0.22,
        source="ClinicalTrials.gov (snapshot diff)",
        timestamp="2026-10-08T12:00:00Z",
        simulated=True,
    ),
    Event(
        gene="IL4R",
        what_changed="New completed Phase 3 result posted for pathway asset",
        before=0.74,
        after=0.78,
        source="ClinicalTrials.gov (snapshot diff)",
        timestamp="2026-10-09T09:30:00Z",
        simulated=True,
    ),
]


def gene_by_id(gene_id: str) -> Optional[Gene]:
    for gene in GENES:
        if gene.id == gene_id or gene.symbol.upper() == gene_id.upper():
            return gene
    return None


def trials_for(gene_id: str) -> List[Trial]:
    gene = gene_by_id(gene_id)
    if gene is None:
        return []
    return TRIALS_BY_GENE.get(gene.id, [])


def judgment_for(gene_id: str) -> Optional[JudgmentCard]:
    gene = gene_by_id(gene_id)
    if gene is None:
        return None
    return JUDGMENT_BY_GENE.get(gene.id) or default_judgment(gene)
