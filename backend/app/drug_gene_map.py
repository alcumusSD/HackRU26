"""Small-scale drug → gene synonyms for demo disease genes.

Used to join ClinicalTrials.gov interventions to Open Targets genes.
Covers asthma + COPD + T2D + RA + Alzheimer demo sets. Expand or replace with
ChEMBL / OT known-drugs when available.
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
    # --- Type 2 diabetes ---
    # GLP-1 receptor agonists (+ dual GIP/GLP-1)
    "semaglutide": ["GLP1R"],
    "ozempic": ["GLP1R"],
    "wegovy": ["GLP1R"],
    "rybelsus": ["GLP1R"],
    "liraglutide": ["GLP1R"],
    "victoza": ["GLP1R"],
    "saxenda": ["GLP1R"],
    "dulaglutide": ["GLP1R"],
    "trulicity": ["GLP1R"],
    "exenatide": ["GLP1R"],
    "byetta": ["GLP1R"],
    "bydureon": ["GLP1R"],
    "lixisenatide": ["GLP1R"],
    "albiglutide": ["GLP1R"],
    "tirzepatide": ["GLP1R"],
    "mounjaro": ["GLP1R"],
    "zepbound": ["GLP1R"],
    # Sulfonylureas / meglitinides → KATP channel (KCNJ11 / ABCC8)
    "glipizide": ["KCNJ11", "ABCC8"],
    "glucotrol": ["KCNJ11", "ABCC8"],
    "glimepiride": ["KCNJ11", "ABCC8"],
    "amaryl": ["KCNJ11", "ABCC8"],
    "glyburide": ["KCNJ11", "ABCC8"],
    "glibenclamide": ["KCNJ11", "ABCC8"],
    "gliclazide": ["KCNJ11", "ABCC8"],
    "tolbutamide": ["KCNJ11", "ABCC8"],
    "chlorpropamide": ["KCNJ11", "ABCC8"],
    "repaglinide": ["KCNJ11", "ABCC8"],
    "prandin": ["KCNJ11", "ABCC8"],
    "nateglinide": ["KCNJ11", "ABCC8"],
    "starlix": ["KCNJ11", "ABCC8"],
    # Thiazolidinediones → PPARG
    "pioglitazone": ["PPARG"],
    "actos": ["PPARG"],
    "rosiglitazone": ["PPARG"],
    "avandia": ["PPARG"],
    "thiazolidinedione": ["PPARG"],
    # Insulin → INSR
    "insulin": ["INSR"],
    "glargine": ["INSR"],
    "lantus": ["INSR"],
    "basaglar": ["INSR"],
    "toujeo": ["INSR"],
    "detemir": ["INSR"],
    "levemir": ["INSR"],
    "degludec": ["INSR"],
    "tresiba": ["INSR"],
    "aspart": ["INSR"],
    "novolog": ["INSR"],
    "lispro": ["INSR"],
    "humalog": ["INSR"],
    "glulisine": ["INSR"],
    "apidra": ["INSR"],
    "nph": ["INSR"],
    "humulin": ["INSR"],
    "novolin": ["INSR"],
    # Metformin → mitochondrial GPD2 (mechanistic target in OT T2D set)
    "metformin": ["GPD2"],
    "glucophage": ["GPD2"],
    "fortamet": ["GPD2"],
    "glumetza": ["GPD2"],
    # --- Rheumatoid arthritis ---
    # TNF inhibitors
    "adalimumab": ["TNF"],
    "humira": ["TNF"],
    "amjevita": ["TNF"],
    "etanercept": ["TNF"],
    "enbrel": ["TNF"],
    "infliximab": ["TNF"],
    "remicade": ["TNF"],
    "inflectra": ["TNF"],
    "certolizumab": ["TNF"],
    "cimzia": ["TNF"],
    "golimumab": ["TNF"],
    "simponi": ["TNF"],
    # IL-6 receptor
    "tocilizumab": ["IL6R"],
    "actemra": ["IL6R"],
    "sarilumab": ["IL6R"],
    "kevzara": ["IL6R"],
    # JAK inhibitors (TYK2 / JAK1 / JAK2)
    "tofacitinib": ["JAK1", "JAK2", "TYK2"],
    "xeljanz": ["JAK1", "JAK2", "TYK2"],
    "baricitinib": ["JAK1", "JAK2", "TYK2"],
    "olumiant": ["JAK1", "JAK2", "TYK2"],
    "upadacitinib": ["JAK1", "JAK2", "TYK2"],
    "rinvoq": ["JAK1", "JAK2", "TYK2"],
    "filgotinib": ["JAK1", "JAK2", "TYK2"],
    "jyseleca": ["JAK1", "JAK2", "TYK2"],
    "deucravacitinib": ["TYK2"],
    "sotyktu": ["TYK2"],
    # IL-12/23 (p40 = IL12B) and IL-23 (IL23A)
    "ustekinumab": ["IL12B", "IL23A"],
    "stelara": ["IL12B", "IL23A"],
    "guselkumab": ["IL23A"],
    "tremfya": ["IL23A"],
    "risankizumab": ["IL23A"],
    "skyrizi": ["IL23A"],
    # IL-17A
    "secukinumab": ["IL17A"],
    "cosentyx": ["IL17A"],
    "ixekizumab": ["IL17A"],
    "taltz": ["IL17A"],
    # COX-2 / NSAIDs → PTGS2
    "celecoxib": ["PTGS2"],
    "celebrex": ["PTGS2"],
    "ibuprofen": ["PTGS2"],
    "naproxen": ["PTGS2"],
    "diclofenac": ["PTGS2"],
    "meloxicam": ["PTGS2"],
    "etoricoxib": ["PTGS2"],
    # MIF antagonists (investigational naming)
    "imilkimod": ["MIF"],
    # --- Alzheimer disease ---
    # Acetylcholinesterase inhibitors → ACHE
    "donepezil": ["ACHE"],
    "aricept": ["ACHE"],
    "rivastigmine": ["ACHE"],
    "exelon": ["ACHE"],
    "galantamine": ["ACHE"],
    "razadyne": ["ACHE"],
    "reminyl": ["ACHE"],
    # NMDA (memantine) → GRIN subunits in OT Alzheimer set
    "memantine": ["GRIN1", "GRIN2B", "GRIN3B"],
    "namenda": ["GRIN1", "GRIN2B", "GRIN3B"],
    "namzaric": ["ACHE", "GRIN1", "GRIN2B", "GRIN3B"],
    # Anti-amyloid monoclonal antibodies → APP
    "lecanemab": ["APP"],
    "leqembi": ["APP"],
    "aducanumab": ["APP"],
    "aduhelm": ["APP"],
    "donanemab": ["APP"],
    "kisunla": ["APP"],
    "gantenerumab": ["APP"],
    "bapineuzumab": ["APP"],
    "solanezumab": ["APP"],
    # Gamma-secretase / PSEN pathway
    "semagacestat": ["PSEN1", "PSEN2", "APH1B"],
    "avagacestat": ["PSEN1", "PSEN2", "APH1B"],
    # BACE1 inhibitors still mention APP pathway in many trial titles
    "verubecestat": ["APP"],
    "atabecestat": ["APP"],
    "lanabecestat": ["APP"],
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
