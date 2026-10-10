"""Shared API contract (partner-roles.md §5 and §17.1)."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Quadrant(str, Enum):
    VALIDATED = "validated"
    WHITE_SPACE = "white_space"
    CAUTION = "caution"
    DEPRIORITIZE = "deprioritize"


class StopReasonCategory(str, Enum):
    LOW_ENROLLMENT = "low_enrollment"
    FUTILITY = "futility"
    SAFETY = "safety"
    BUSINESS = "business"
    OTHER = "other"


class ConfidenceBand(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    THIN = "thin"


class CardConfidence(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class ScoreBreakdownItem(BaseModel):
    component: str
    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)


class Gene(BaseModel):
    id: str
    symbol: str
    genetic_score: float = Field(ge=0.0, le=1.0)
    activity_score: float = Field(ge=0.0, le=1.0)
    score_breakdown: List[ScoreBreakdownItem] = Field(default_factory=list)
    protective_variant: bool = False
    quadrant: Quadrant
    contradictions: List[str] = Field(default_factory=list)
    partial_data: bool = False
    safety_flag: bool = False


class Trial(BaseModel):
    nct_id: str
    phase: str
    status: str
    drugs: List[str] = Field(default_factory=list)
    target_genes: List[str] = Field(default_factory=list)
    stop_reason_category: Optional[StopReasonCategory] = None
    stop_reason_quote: Optional[str] = None
    quote_verified: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Event(BaseModel):
    gene: str
    what_changed: str
    before: float
    after: float
    source: str
    timestamp: str
    simulated: bool = False


class EvidenceItem(BaseModel):
    text: str
    source: str
    date: str
    evidence_type: Literal["gwas", "trial", "database", "ai_read"]


class AgainstItem(BaseModel):
    id: str
    text: str
    quote: str
    quote_verified: bool
    source: str
    kind: Literal["failed_trial", "contradiction", "safety", "stale"]


class CouldChangeIf(BaseModel):
    event: str
    effect: str


class Conflict(BaseModel):
    claim_a: str
    claim_b: str
    difference: Literal["population", "method", "date"]


class Robustness(BaseModel):
    top_k: int = 5
    runs: int = 1000
    share_in_top_k: float = Field(ge=0.0, le=1.0)
    label: Literal["stable", "moderate", "fragile"] = "moderate"
    rank_p5: Optional[int] = None
    rank_p95: Optional[int] = None


class JudgmentCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    gene_id: str
    confidence: ConfidenceBand
    robustness: Robustness
    for_: List[EvidenceItem] = Field(
        default_factory=list,
        alias="for",
        serialization_alias="for",
    )
    against: List[AgainstItem] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    could_change_if: List[CouldChangeIf] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    data_as_of: str
    card_confidence: CardConfidence


class GeneListResponse(BaseModel):
    disease: str
    data_as_of: str
    cached: bool = True
    genes: List[Gene]


class HealthResponse(BaseModel):
    status: str
    service: str
    mode: str
