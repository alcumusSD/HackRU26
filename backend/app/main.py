"""Evidence Radar FastAPI — mock mode for hour-1 UI unblock."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.mock_data import (
    DATA_AS_OF,
    DISEASE,
    EVENTS,
    GENES,
    gene_by_id,
    judgment_for,
    trials_for,
)
from app.models import (
    Event,
    Gene,
    GeneListResponse,
    HealthResponse,
    JudgmentCard,
    Robustness,
    Trial,
)

app = FastAPI(
    title="Evidence Radar API",
    description="Mock-backed API for Evidence Radar + Trials. Live fetch comes later.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_config() -> Dict:
    config_path = Path(__file__).resolve().parents[1] / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {"disease": {"name": DISEASE}, "data_as_of": DATA_AS_OF}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="evidence-radar", mode="mock")


@app.get("/genes", response_model=GeneListResponse)
def list_genes(
    disease: str = Query(default=DISEASE, description="Disease name or EFO id"),
) -> GeneListResponse:
    config = _load_config()
    expected = config.get("disease", {}).get("name", DISEASE).lower()
    if disease.lower() not in {expected, "asthma", "efo_0000270"}:
        raise HTTPException(
            status_code=404,
            detail=f"Disease '{disease}' not in mock set. Try disease=asthma",
        )
    return GeneListResponse(
        disease=expected,
        data_as_of=config.get("data_as_of", DATA_AS_OF),
        cached=True,
        genes=GENES,
    )


@app.get("/genes/{gene_id}", response_model=Gene)
def get_gene(gene_id: str) -> Gene:
    gene = gene_by_id(gene_id)
    if gene is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return gene


@app.get("/genes/{gene_id}/trials", response_model=List[Trial])
def get_trials(gene_id: str) -> List[Trial]:
    if gene_by_id(gene_id) is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return trials_for(gene_id)


@app.get("/genes/{gene_id}/judgment", response_model=JudgmentCard)
def get_judgment(gene_id: str) -> JudgmentCard:
    card = judgment_for(gene_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return card


@app.get("/genes/{gene_id}/robustness", response_model=Robustness)
def get_robustness(gene_id: str) -> Robustness:
    card = judgment_for(gene_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return card.robustness


@app.get("/events", response_model=List[Event])
def list_events() -> List[Event]:
    return EVENTS
