"""Load genes/trials from processed cache or fall back to mocks.

Cached mode assembles judgment cards from real gene + trial fields.
Supports per-disease paths under data/processed/<slug>/.
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
    DiseaseInfo,
    Gene,
    JudgmentCard,
    NetworkLink,
    NetworkNode,
    NetworkResponse,
    Trial,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_RAW = ROOT / "data" / "raw"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"

# In-memory cache keyed by disease slug
_genes_cache: Dict[str, List[Gene]] = {}
_trials_cache: Dict[str, Dict[str, List[Trial]]] = {}


def load_config() -> Dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {
        "default_disease": "asthma",
        "diseases": {"asthma": {"name": DISEASE, "efo_id": "", "label": "Asthma"}},
        "data_as_of": DATA_AS_OF,
    }


def default_disease_slug() -> str:
    config = load_config()
    return str(config.get("default_disease") or "asthma")


def list_disease_infos() -> List[DiseaseInfo]:
    config = load_config()
    diseases = config.get("diseases") or {}
    if not diseases and config.get("disease"):
        d = config["disease"]
        return [
            DiseaseInfo(
                slug=str(d.get("name") or "asthma").lower(),
                label=str(d.get("label") or d.get("name") or "asthma"),
                efo_id=str(d.get("efo_id") or ""),
                name=str(d.get("name") or "asthma"),
            )
        ]
    out: List[DiseaseInfo] = []
    for slug, entry in diseases.items():
        out.append(
            DiseaseInfo(
                slug=slug,
                label=str(entry.get("label") or entry.get("name") or slug),
                efo_id=str(entry.get("efo_id") or ""),
                name=str(entry.get("name") or slug),
            )
        )
    # Prefer default first
    default = default_disease_slug()
    out.sort(key=lambda d: (0 if d.slug == default else 1, d.label.lower()))
    return out


def resolve_disease_slug(disease: Optional[str] = None) -> str:
    """Map query string (slug, name, or efo_id) to a configured disease slug."""
    config = load_config()
    diseases = config.get("diseases") or {}
    needle = (disease or default_disease_slug()).strip().lower()

    if not diseases:
        legacy = config.get("disease") or {}
        aliases = {
            str(legacy.get("name") or "asthma").lower(),
            str(legacy.get("efo_id") or "").lower(),
            "asthma",
        }
        aliases.discard("")
        if needle in aliases:
            return str(legacy.get("name") or "asthma").lower()
        raise KeyError(disease or needle)

    for slug, entry in diseases.items():
        aliases = {
            slug.lower(),
            str(entry.get("name") or "").lower(),
            str(entry.get("label") or "").lower(),
            str(entry.get("efo_id") or "").lower(),
        }
        aliases.discard("")
        if needle in aliases:
            return slug

    raise KeyError(disease or needle)


def processed_paths(slug: str) -> Tuple[Path, Path]:
    return (
        DATA_PROCESSED / slug / "genes.json",
        DATA_PROCESSED / slug / "trials_by_gene.json",
    )


def migrate_legacy_paths() -> None:
    """Best-effort move of flat cache into asthma/ (API side safety net)."""
    legacy_genes = DATA_PROCESSED / "genes.json"
    legacy_trials = DATA_PROCESSED / "trials_by_gene.json"
    dest_genes = DATA_PROCESSED / "asthma" / "genes.json"
    dest_trials = DATA_PROCESSED / "asthma" / "trials_by_gene.json"
    if legacy_genes.exists() and not dest_genes.exists():
        dest_genes.parent.mkdir(parents=True, exist_ok=True)
        legacy_genes.rename(dest_genes)
    if legacy_trials.exists() and not dest_trials.exists():
        dest_trials.parent.mkdir(parents=True, exist_ok=True)
        legacy_trials.rename(dest_trials)

    for name in ("genes.json", "trials.json"):
        legacy = DATA_RAW / name
        dest = DATA_RAW / "asthma" / name
        if legacy.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            legacy.rename(dest)


def resolve_mode() -> str:
    mode = os.getenv("DATA_MODE", "auto").strip().lower()
    if mode not in {"mock", "cached", "auto"}:
        return "auto"
    return mode


def _load_processed_genes(slug: str) -> Optional[List[Gene]]:
    genes_path, _ = processed_paths(slug)
    if not genes_path.exists():
        # Fall back to legacy flat path for asthma only
        if slug == "asthma":
            legacy = DATA_PROCESSED / "genes.json"
            if legacy.exists():
                genes_path = legacy
            else:
                return None
        else:
            return None
    payload = json.loads(genes_path.read_text())
    items = payload.get("genes") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return None
    return [Gene.model_validate(item) for item in items]


def _load_trials_by_gene(slug: str) -> Dict[str, List[Trial]]:
    _, trials_path = processed_paths(slug)
    if not trials_path.exists():
        if slug == "asthma":
            legacy = DATA_PROCESSED / "trials_by_gene.json"
            if legacy.exists():
                trials_path = legacy
            else:
                return {}
        else:
            return {}
    payload = json.loads(trials_path.read_text())
    raw_map = payload.get("trials_by_gene") or {}
    out: Dict[str, List[Trial]] = {}
    for gene_id, items in raw_map.items():
        out[gene_id] = [Trial.model_validate(item) for item in items]
    return out


def active_mode(disease: Optional[str] = None) -> str:
    migrate_legacy_paths()
    mode = resolve_mode()
    try:
        slug = resolve_disease_slug(disease)
    except KeyError:
        slug = default_disease_slug()
    genes_path, _ = processed_paths(slug)
    has_cache = genes_path.exists() or (
        slug == "asthma" and (DATA_PROCESSED / "genes.json").exists()
    )
    if mode == "auto":
        return "cached" if has_cache else "mock"
    if mode == "cached" and not has_cache:
        return "mock"
    return mode


def _genes_for(slug: str) -> List[Gene]:
    if slug in _genes_cache:
        return _genes_cache[slug]
    if active_mode(slug) == "cached":
        genes = _load_processed_genes(slug)
        if genes:
            _genes_cache[slug] = genes
            return genes
    if slug == default_disease_slug() or slug == "asthma":
        return list(MOCK_GENES)
    return []


def list_genes(disease: Optional[str] = None) -> List[Gene]:
    slug = resolve_disease_slug(disease)
    return list(_genes_for(slug))


def get_gene(gene_id: str, disease: Optional[str] = None) -> Optional[Gene]:
    needle = gene_id.upper()
    for gene in list_genes(disease):
        if gene.id.upper() == needle or gene.symbol.upper() == needle:
            return gene
    return None


def get_trials(gene_id: str, disease: Optional[str] = None) -> List[Trial]:
    slug = resolve_disease_slug(disease)
    gene = get_gene(gene_id, slug)
    if gene is None:
        return []

    if active_mode(slug) == "cached":
        if slug not in _trials_cache:
            _trials_cache[slug] = _load_trials_by_gene(slug)
        by_id = _trials_cache[slug]
        if gene.id in by_id:
            return by_id[gene.id]
        for key, trials in by_id.items():
            if key.upper() == gene.id.upper():
                return trials

    mock = mock_gene_by_id(gene.id) or mock_gene_by_id(gene.symbol)
    if mock is not None:
        return mock_trials_for(mock.id)
    return []


def get_judgment(gene_id: str, disease: Optional[str] = None) -> Optional[JudgmentCard]:
    slug = resolve_disease_slug(disease)
    gene = get_gene(gene_id, slug)
    if gene is None:
        return None

    m = meta(slug)
    if active_mode(slug) == "cached":
        trials = get_trials(gene.id, slug)
        return assemble_judgment(
            gene,
            trials,
            data_as_of=m["data_as_of"],
            peers=list_genes(slug),
        )

    if mock_gene_by_id(gene.id) or mock_gene_by_id(gene.symbol):
        return mock_judgment_for(gene.id) or mock_judgment_for(gene.symbol)
    return default_judgment(gene)


def meta(disease: Optional[str] = None) -> Dict:
    config = load_config()
    try:
        slug = resolve_disease_slug(disease)
    except KeyError:
        slug = default_disease_slug()
    mode = active_mode(slug)
    _, trials_path = processed_paths(slug)
    has_trials = trials_path.exists() or (
        slug == "asthma" and (DATA_PROCESSED / "trials_by_gene.json").exists()
    )
    source = "mock"
    if mode == "cached":
        source = "open_targets+clinicaltrials" if has_trials else "open_targets"

    diseases = config.get("diseases") or {}
    entry = diseases.get(slug) or config.get("disease") or {}
    display_name = entry.get("name") or slug

    return {
        "mode": mode,
        "disease": display_name,
        "disease_slug": slug,
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
    "asthma controller therapies",
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


def build_network(
    disease: Optional[str] = None,
    max_drugs: int = 14,
    min_edge_weight: int = 2,
) -> NetworkResponse:
    """Gene–drug network from linked trials (different view than score map).

    Kept intentionally sparse: top drugs by trial volume, edges with enough
    supporting trials, and only genes that still have a drug link.
    """
    slug = resolve_disease_slug(disease)
    m = meta(slug)
    genes = list_genes(slug)
    edges: Dict[Tuple[str, str], Dict] = {}
    drug_counts: Dict[str, int] = defaultdict(int)
    gene_trial_counts: Dict[str, int] = defaultdict(int)
    drug_gene_sets: Dict[str, Set[str]] = defaultdict(set)

    for gene in genes:
        trials = get_trials(gene.id, slug)
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
