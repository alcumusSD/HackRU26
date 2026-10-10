"""Small-scale drug → gene synonyms for demo disease genes.

Used to join ClinicalTrials.gov interventions to Open Targets genes.
Covers asthma + COPD demo sets. Expand or replace with ChEMBL / OT known-drugs
when available.
"""

from __future__ import annotations

from typing import Dict, List, Set

# Lowercase drug / intervention tokens → gene symbols in our demo set.
DRUG_TO_GENES: Dict[str, List[str]] = {
    # IL4R / IL13 pathway
    "dupilumab": ["IL4R", "IL13"],
    "dupixent": ["IL4R", "IL13"],
    "pitrakinra": ["IL4R"],
    "altrakincept": ["IL4R"],
    "lebrikizumab": ["IL13"],
    "tralokinumab": ["IL13"],
    "anrukinzumab": ["IL13"],
    # IL5 / eosinophil
    "mepolizumab": ["IL5"],
    "nucala": ["IL5"],
    "reslizumab": ["IL5"],
    "cinqair": ["IL5"],
    "cinqaero": ["IL5"],
    "benralizumab": ["IL5"],
    "fasenra": ["IL5"],
    # TSLP
    "tezepelumab": ["TSLP"],
    "tezir": ["TSLP"],
    "tezsire": ["TSLP"],
    # IL33
    "itepekimab": ["IL33"],
    "tozorakimab": ["IL33"],
    "astegolimab": ["IL33"],
    # IgE
    "omalizumab": ["IGHE"],
    "xolair": ["IGHE"],
    "ligelizumab": ["IGHE"],
    # ADRB2
    "albuterol": ["ADRB2"],
    "salbutamol": ["ADRB2"],
    "levalbuterol": ["ADRB2"],
    "formoterol": ["ADRB2"],
    "salmeterol": ["ADRB2"],
    "indacaterol": ["ADRB2"],
    "olodaterol": ["ADRB2"],
    "vilanterol": ["ADRB2"],
    "epinephrine": ["ADRB2"],
    # CYSLTR1
    "montelukast": ["CYSLTR1"],
    "singulair": ["CYSLTR1"],
    "zafirlukast": ["CYSLTR1"],
    "accolate": ["CYSLTR1"],
    "pranlukast": ["CYSLTR1"],
    # PDE4 (+ ensifentrine PDE3/4 dual)
    "roflumilast": ["PDE4D", "PDE4A", "PDE4B"],
    "daliresp": ["PDE4D", "PDE4A", "PDE4B"],
    "apremilast": ["PDE4D", "PDE4A", "PDE4B"],
    "ensifentrine": ["PDE4D", "PDE4A", "PDE4B"],
    "ohtuvayre": ["PDE4D", "PDE4A", "PDE4B"],
    # Muscarinic (LAMAs primarily target CHRM3)
    "tiotropium": ["CHRM3", "CHRM1", "CHRM2"],
    "spiriva": ["CHRM3", "CHRM1", "CHRM2"],
    "ipratropium": ["CHRM3", "CHRM1", "CHRM2"],
    "atrovent": ["CHRM3", "CHRM1", "CHRM2"],
    "umeclidinium": ["CHRM3", "CHRM1", "CHRM2"],
    "glycopyrronium": ["CHRM3", "CHRM1", "CHRM2"],
    "glycopyrrolate": ["CHRM3", "CHRM1", "CHRM2"],
    "aclidinium": ["CHRM3", "CHRM1", "CHRM2"],
    "revefenacin": ["CHRM3", "CHRM1", "CHRM2"],
    # Glucocorticoid receptor
    "budesonide": ["NR3C1"],
    "fluticasone": ["NR3C1"],
    "beclomethasone": ["NR3C1"],
    "mometasone": ["NR3C1"],
    "ciclesonide": ["NR3C1"],
    "prednisone": ["NR3C1"],
    "prednisolone": ["NR3C1"],
    "methylprednisolone": ["NR3C1"],
    "dexamethasone": ["NR3C1"],
    # Adenosine
    "theophylline": ["ADORA1"],
    "aminophylline": ["ADORA1"],
    # CFTR modulators (COPD OT set includes CFTR)
    "ivacaftor": ["CFTR"],
    "kalydeco": ["CFTR"],
    "lumacaftor": ["CFTR"],
    "orkambi": ["CFTR"],
    "tezacaftor": ["CFTR"],
    "symdeko": ["CFTR"],
    "elexacaftor": ["CFTR"],
    "trikafta": ["CFTR"],
    # Alpha-1 antitrypsin (SERPINA1)
    "alpha1": ["SERPINA1"],
    "alpha-1": ["SERPINA1"],
    "antitrypsin": ["SERPINA1"],
    "prolastin": ["SERPINA1"],
    "aralast": ["SERPINA1"],
    "glassia": ["SERPINA1"],
    "zemaira": ["SERPINA1"],
    "respreeza": ["SERPINA1"],
    # ENaC (SCNN1*)
    "amiloride": ["SCNN1A", "SCNN1B", "SCNN1G"],
    "benzamil": ["SCNN1A", "SCNN1B", "SCNN1G"],
    # Nicotinic (CHRNA4)
    "varenicline": ["CHRNA4"],
    "chantix": ["CHRNA4"],
    "nicotine": ["CHRNA4"],
}

# Normalize keys
DRUG_TO_GENES = {k.lower(): v for k, v in DRUG_TO_GENES.items()}


def normalize_name(text: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())


def genes_for_intervention(name: str, demo_symbols: Set[str]) -> Set[str]:
    """Return demo gene symbols linked to an intervention name."""
    norm = normalize_name(name)
    hits: Set[str] = set()
    if not norm:
        return hits

    for token, genes in DRUG_TO_GENES.items():
        if token in norm:
            hits.update(g for g in genes if g in demo_symbols)

    compact = norm.replace(" ", "").replace("-", "")
    for symbol in demo_symbols:
        sym = symbol.lower()
        if sym in compact:
            hits.add(symbol)
            continue
        if symbol.upper().startswith("IL") and len(symbol) > 2:
            dashed = f"il-{symbol[2:]}".lower()
            spaced = f"il {symbol[2:]}".lower()
            if dashed in norm or spaced in norm:
                hits.add(symbol)

    return hits
