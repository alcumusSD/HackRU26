"""Evidence Radar FastAPI — mock or Open Targets cached genes; judgment/trials mock."""

from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import data_store
from app.mock_data import EVENTS
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
    description=(
        "Evidence Radar + Trials API. Genes may come from Open Targets cache; "
        "judgment and trials remain mock/default until those pipelines are wired."
    ),
    version="0.2.0",
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


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    meta = data_store.meta()
    return HealthResponse(
        status="ok",
        service="evidence-radar",
        mode=meta["mode"],
    )


@app.get("/genes", response_model=GeneListResponse)
def list_genes(
    disease: str = Query(default="asthma", description="Disease name or ontology id"),
) -> GeneListResponse:
    meta = data_store.meta()
    expected = meta["disease"].lower()
    disease_l = disease.lower()
    config = data_store.load_config()
    efo = (config.get("disease") or {}).get("efo_id", "").lower()
    if disease_l not in {expected, "asthma", efo, "mondo_0004979", "efo_0000270"}:
        raise HTTPException(
            status_code=404,
            detail=f"Disease '{disease}' not configured. Try disease=asthma",
        )
    return GeneListResponse(
        disease=meta["disease"],
        data_as_of=meta["data_as_of"],
        cached=True,
        genes=data_store.list_genes(),
    )


@app.get("/genes/{gene_id}", response_model=Gene)
def get_gene(gene_id: str) -> Gene:
    gene = data_store.get_gene(gene_id)
    if gene is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return gene


@app.get("/genes/{gene_id}/trials", response_model=List[Trial])
def get_trials(gene_id: str) -> List[Trial]:
    if data_store.get_gene(gene_id) is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return data_store.get_trials(gene_id)


@app.get("/genes/{gene_id}/judgment", response_model=JudgmentCard)
def get_judgment(gene_id: str) -> JudgmentCard:
    card = data_store.get_judgment(gene_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return card


@app.get("/genes/{gene_id}/robustness", response_model=Robustness)
def get_robustness(gene_id: str) -> Robustness:
    card = data_store.get_judgment(gene_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return card.robustness


@app.get("/events", response_model=List[Event])
def list_events() -> List[Event]:
    return EVENTS
