"""Load genes from processed cache or fall back to mocks. Judgment/trials stay mock-backed."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from app.mock_data import (
    DATA_AS_OF,
    DISEASE,
    GENES as MOCK_GENES,
    default_judgment,
    gene_by_id as mock_gene_by_id,
    judgment_for as mock_judgment_for,
    trials_for as mock_trials_for,
)
from app.models import Gene, JudgmentCard, Trial

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_GENES = ROOT / "data" / "processed" / "genes.json"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


def load_config() -> Dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"disease": {"name": DISEASE}, "data_as_of": DATA_AS_OF}


def resolve_mode() -> str:
    """mock | cached | auto (cached if processed file exists)."""
    mode = os.getenv("DATA_MODE", "auto").strip().lower()
    if mode not in {"mock", "cached", "auto"}:
        return "auto"
    return mode


def _load_processed_genes() -> Optional[List[Gene]]:
    if not PROCESSED_GENES.exists():
        return None
    payload = json.loads(PROCESSED_GENES.read_text())
    items = payload.get("genes") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return None
    return [Gene.model_validate(item) for item in items]


def active_mode() -> str:
    mode = resolve_mode()
    if mode == "auto":
        return "cached" if PROCESSED_GENES.exists() else "mock"
    if mode == "cached" and not PROCESSED_GENES.exists():
        return "mock"
    return mode


def list_genes() -> List[Gene]:
    if active_mode() == "cached":
        genes = _load_processed_genes()
        if genes:
            return genes
    return list(MOCK_GENES)


def get_gene(gene_id: str) -> Optional[Gene]:
    needle = gene_id.upper()
    for gene in list_genes():
        if gene.id.upper() == needle or gene.symbol.upper() == needle:
            return gene
    return None


def get_trials(gene_id: str) -> List[Trial]:
    """Prefer mock trial stories when the gene exists in mocks; else empty."""
    gene = get_gene(gene_id)
    if gene is None:
        return []
    mock = mock_gene_by_id(gene.id) or mock_gene_by_id(gene.symbol)
    if mock is not None:
        return mock_trials_for(mock.id)
    return []


def get_judgment(gene_id: str) -> Optional[JudgmentCard]:
    gene = get_gene(gene_id)
    if gene is None:
        return None
    mock_card = mock_judgment_for(gene.id) or mock_judgment_for(gene.symbol)
    # mock_judgment_for always returns a card for known mock genes via default_judgment
    if mock_gene_by_id(gene.id) or mock_gene_by_id(gene.symbol):
        return mock_card
    return default_judgment(gene)


def meta() -> Dict:
    config = load_config()
    mode = active_mode()
    return {
        "mode": mode,
        "disease": config.get("disease", {}).get("name", DISEASE),
        "data_as_of": config.get("data_as_of", DATA_AS_OF),
        "cached": mode == "cached",
        "source": "open_targets_processed" if mode == "cached" else "mock",
    }
