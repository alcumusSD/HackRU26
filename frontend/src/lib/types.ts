export type Quadrant =
  | "validated"
  | "white_space"
  | "caution"
  | "deprioritize";

export type ScoreBreakdownItem = {
  component: string;
  value: number;
  weight: number;
  sources: string[];
};

export type Gene = {
  id: string;
  symbol: string;
  genetic_score: number;
  activity_score: number;
  score_breakdown: ScoreBreakdownItem[];
  protective_variant: boolean;
  quadrant: Quadrant;
  contradictions: string[];
  partial_data: boolean;
  safety_flag: boolean;
};

export type GeneListResponse = {
  disease: string;
  data_as_of: string;
  cached: boolean;
  genes: Gene[];
};

export type Trial = {
  nct_id: string;
  phase: string;
  status: string;
  drugs: string[];
  target_genes: string[];
  stop_reason_category:
    | "low_enrollment"
    | "futility"
    | "safety"
    | "business"
    | "other"
    | null;
  stop_reason_quote: string | null;
  quote_verified: boolean;
  start_date: string | null;
  end_date: string | null;
};

export type JudgmentCard = {
  gene_id: string;
  confidence: "strong" | "moderate" | "thin";
  robustness: {
    top_k: number;
    runs: number;
    share_in_top_k: number;
    label: "stable" | "moderate" | "fragile";
    rank_p5: number | null;
    rank_p95: number | null;
  };
  for: {
    text: string;
    source: string;
    date: string;
    evidence_type: string;
  }[];
  against: {
    id: string;
    text: string;
    quote: string;
    quote_verified: boolean;
    source: string;
    kind: string;
  }[];
  missing: string[];
  could_change_if: { event: string; effect: string }[];
  conflicts: {
    claim_a: string;
    claim_b: string;
    difference: string;
  }[];
  open_questions: string[];
  data_as_of: string;
  card_confidence: "high" | "moderate" | "low";
};
