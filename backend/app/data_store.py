"""Load genes/trials from processed cache or fall back to mocks.

Cached mode assembles judgment cards from real gene + trial fields.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from app.judgment import assemble_judgment
from app.mock_data import (
    DATA_AS_OF,
    DISEASE,
    GENES as MOCK_GENES,
    default_judgment,
    gene_by_id as mock_gene_by_id,
    judgment_for as mock_judgment_for,
    trials_for as mock_trials_for,
)
from app.models import (
    Gene,
    JudgmentCard,
    NetworkLink,
    NetworkNode,
    NetworkResponse,
    Trial,
)

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_GENES = ROOT / "data" / "processed" / "genes.json"
PROCESSED_TRIALS = ROOT / "data" / "processed" / "trials_by_gene.json"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


def load_config() -> Dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"disease": {"name": DISEASE}, "data_as_of": DATA_AS_OF}


def resolve_mode() -> str:
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


def _load_trials_by_gene() -> Dict[str, List[Trial]]:
    if not PROCESSED_TRIALS.exists():
        return {}
    payload = json.loads(PROCESSED_TRIALS.read_text())
    raw_map = payload.get("trials_by_gene") or {}
    out: Dict[str, List[Trial]] = {}
    for gene_id, items in raw_map.items():
        out[gene_id] = [Trial.model_validate(item) for item in items]
    return out


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
    gene = get_gene(gene_id)
    if gene is None:
        return []

    if active_mode() == "cached":
        by_id = _load_trials_by_gene()
        if gene.id in by_id:
            return by_id[gene.id]
        # Also allow lookup if map keyed oddly
        for key, trials in by_id.items():
            if key.upper() == gene.id.upper():
                return trials

    mock = mock_gene_by_id(gene.id) or mock_gene_by_id(gene.symbol)
    if mock is not None:
        return mock_trials_for(mock.id)
    return []


def get_judgment(gene_id: str) -> Optional[JudgmentCard]:
    gene = get_gene(gene_id)
    if gene is None:
        return None

    m = meta()
    if active_mode() == "cached":
        trials = get_trials(gene.id)
        return assemble_judgment(
            gene,
            trials,
            data_as_of=m["data_as_of"],
            peers=list_genes(),
        )

    # Mock mode: keep narrative fixtures for the demo gene set.
    if mock_gene_by_id(gene.id) or mock_gene_by_id(gene.symbol):
        return mock_judgment_for(gene.id) or mock_judgment_for(gene.symbol)
    return default_judgment(gene)


def meta() -> Dict:
    config = load_config()
    mode = active_mode()
    has_trials = PROCESSED_TRIALS.exists()
    source = "mock"
    if mode == "cached":
        source = "open_targets+clinicaltrials" if has_trials else "open_targets"
    return {
        "mode": mode,
        "disease": config.get("disease", {}).get("name", DISEASE),
        "data_as_of": config.get("data_as_of", DATA_AS_OF),
        "cached": mode == "cached",
        "source": source,
    }


_SKIP_DRUGS = {
    "placebo",
    "none",
    "n/a",
    "none (observational study)",
    "no intervention: observational cohort",
    "asthma reliever therapies",
}


def normalize_drug_name(name: str) -> Optional[str]:
    raw = (name or "").strip()
    if not raw:
        return None
    lower = raw.lower()
    if lower in _SKIP_DRUGS:
        return None
    # Keep primary agent before slash / dose clutter
    primary = lower.split("/")[0]
    primary = re.split(r"\d", primary, maxsplit=1)[0]
    primary = re.sub(r"\s+", " ", primary).strip(" -_")
    if len(primary) < 3 or primary in _SKIP_DRUGS:
        return None
    return primary.title()


def build_network(max_drugs: int = 14, min_edge_weight: int = 2) -> NetworkResponse:
    """Gene–drug network from linked trials (different view than score map).

    Kept intentionally sparse: top drugs by trial volume, edges with enough
    supporting trials, and only genes that still have a drug link.
    """
    m = meta()
    genes = list_genes()
    edges: Dict[Tuple[str, str], Dict] = {}
    drug_counts: Dict[str, int] = defaultdict(int)
    gene_trial_counts: Dict[str, int] = defaultdict(int)
    drug_gene_sets: Dict[str, Set[str]] = defaultdict(set)

    for gene in genes:
        trials = get_trials(gene.id)
        gene_trial_counts[gene.id] = len(trials)
        gene_node = f"gene:{gene.symbol}"
        for trial in trials:
            for drug_raw in trial.drugs or []:
                drug = normalize_drug_name(drug_raw)
                if not drug:
                    continue
                drug_node = f"drug:{drug.lower()}"
                drug_counts[drug_node] += 1
                drug_gene_sets[drug_node].add(gene_node)
                key = (gene_node, drug_node)
                if key not in edges:
                    edges[key] = {
                        "source": gene_node,
                        "target": drug_node,
                        "weight": 0,
                        "sample_ncts": [],
                        "drug_name": drug,
                        "gene": gene,
                    }
                edges[key]["weight"] += 1
                ncts: List[str] = edges[key]["sample_ncts"]
                if trial.nct_id not in ncts and len(ncts) < 12:
                    ncts.append(trial.nct_id)

    # Prefer multi-gene hub drugs, then fill with highest trial volume
    ranked_drugs = sorted(
        drug_counts.keys(),
        key=lambda d: (-len(drug_gene_sets[d]), -drug_counts[d], d),
    )
    top_drugs: Set[str] = set(ranked_drugs[:max_drugs])

    gene_nodes: Dict[str, NetworkNode] = {}
    drug_nodes: Dict[str, NetworkNode] = {}
    links: List[NetworkLink] = []
    degree: Dict[str, int] = defaultdict(int)

    for _key, meta_edge in edges.items():
        if meta_edge["target"] not in top_drugs:
            continue
        if meta_edge["weight"] < min_edge_weight:
            continue
        gene: Gene = meta_edge["gene"]
        g_id = meta_edge["source"]
        d_id = meta_edge["target"]
        if g_id not in gene_nodes:
            gene_nodes[g_id] = NetworkNode(
                id=g_id,
                name=gene.symbol,
                kind="gene",
                gene_id=gene.id,
                symbol=gene.symbol,
                quadrant=gene.quadrant,
                genetic_score=gene.genetic_score,
                activity_score=gene.activity_score,
                trial_count=gene_trial_counts.get(gene.id, 0),
            )
        if d_id not in drug_nodes:
            drug_nodes[d_id] = NetworkNode(
                id=d_id,
                name=meta_edge["drug_name"],
                kind="drug",
                trial_count=drug_counts.get(d_id, 0),
            )
        links.append(
            NetworkLink(
                source=g_id,
                target=d_id,
                weight=meta_edge["weight"],
                sample_ncts=meta_edge["sample_ncts"],
            )
        )
        degree[g_id] += 1
        degree[d_id] += 1

    # Drop drugs that lost all edges after the weight filter
    drug_nodes = {d_id: node for d_id, node in drug_nodes.items() if degree[d_id] > 0}

    nodes = []
    for node in list(gene_nodes.values()) + list(drug_nodes.values()):
        node.degree = degree.get(node.id, 0)
        nodes.append(node)

    return NetworkResponse(
        disease=m["disease"],
        data_as_of=m["data_as_of"],
        description=(
            f"Top {max_drugs} drugs by clinical reach (≥{min_edge_weight} shared trials per link). "
            "Shows clinical neighborhood, not evidence×activity."
        ),
        nodes=nodes,
        links=links,
    )
