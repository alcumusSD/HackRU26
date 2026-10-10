"""Evidence Radar FastAPI — cached OT/CT.gov genes; optional Gemini chat."""

from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.env_load import load_app_env

load_app_env()

from app import data_store
from app.gemini_client import (
    answer_about_context,
    gemini_status,
    get_model_name,
    ping as gemini_ping,
)
from app.mock_data import EVENTS
from app.models import (
    ChatRequest,
    ChatResponse,
    DiseaseInfo,
    Event,
    Gene,
    GeneListResponse,
    HealthResponse,
    JudgmentCard,
    NetworkResponse,
    Robustness,
    Trial,
)

app = FastAPI(
    title="Evidence Radar API",
    description=(
        "Evidence Radar + Trials API. Genes/trials from Open Targets + CT.gov; "
        "optional grounded Gemini chat over the UI context. Judgment cards remain "
        "mock/default until that pipeline is wired."
    ),
    version="0.4.0",
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


def _require_disease(disease: Optional[str]) -> str:
    try:
        return data_store.resolve_disease_slug(disease)
    except KeyError:
        known = ", ".join(d.slug for d in data_store.list_disease_infos()) or "asthma"
        raise HTTPException(
            status_code=404,
            detail=f"Disease '{disease}' not configured. Try: {known}",
        ) from None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    meta = data_store.meta()
    return HealthResponse(
        status="ok",
        service="evidence-radar",
        mode=meta["mode"],
        gemini=gemini_status(),
    )


@app.get("/diseases", response_model=List[DiseaseInfo])
def list_diseases() -> List[DiseaseInfo]:
    return data_store.list_disease_infos()


@app.get("/gemini/ping")
def gemini_ping_route() -> dict:
    """Live Gemini smoke test (does not return the API key)."""
    if gemini_status() != "configured":
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY missing or placeholder in backend/.env",
        )
    try:
        return gemini_ping()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Answer questions using only the provided on-screen context."""
    if gemini_status() != "configured":
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY missing or placeholder in backend/.env",
        )
    history = [{"role": m.role, "content": m.content} for m in req.history]
    try:
        reply = answer_about_context(req.message, req.context, history)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(reply=reply, model=get_model_name(), grounded=True)


@app.get("/genes", response_model=GeneListResponse)
def list_genes(
    disease: Optional[str] = Query(
        default=None,
        description="Disease slug, name, or ontology id",
    ),
) -> GeneListResponse:
    slug = _require_disease(disease or data_store.default_disease_slug())
    meta = data_store.meta(slug)
    return GeneListResponse(
        disease=meta["disease"],
        data_as_of=meta["data_as_of"],
        cached=meta["cached"],
        genes=data_store.list_genes(slug),
    )


@app.get("/genes/{gene_id}", response_model=Gene)
def get_gene(
    gene_id: str,
    disease: Optional[str] = Query(default=None, description="Disease slug"),
) -> Gene:
    slug = _require_disease(disease or data_store.default_disease_slug())
    gene = data_store.get_gene(gene_id, slug)
    if gene is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return gene


@app.get("/genes/{gene_id}/trials", response_model=List[Trial])
def get_trials(
    gene_id: str,
    disease: Optional[str] = Query(default=None, description="Disease slug"),
) -> List[Trial]:
    slug = _require_disease(disease or data_store.default_disease_slug())
    if data_store.get_gene(gene_id, slug) is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return data_store.get_trials(gene_id, slug)


@app.get("/genes/{gene_id}/judgment", response_model=JudgmentCard)
def get_judgment(
    gene_id: str,
    disease: Optional[str] = Query(default=None, description="Disease slug"),
) -> JudgmentCard:
    slug = _require_disease(disease or data_store.default_disease_slug())
    card = data_store.get_judgment(gene_id, slug)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return card


@app.get("/genes/{gene_id}/robustness", response_model=Robustness)
def get_robustness(
    gene_id: str,
    disease: Optional[str] = Query(default=None, description="Disease slug"),
) -> Robustness:
    slug = _require_disease(disease or data_store.default_disease_slug())
    card = data_store.get_judgment(gene_id, slug)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Gene '{gene_id}' not found")
    return card.robustness


@app.get("/events", response_model=List[Event])
def list_events() -> List[Event]:
    return EVENTS


@app.get("/network", response_model=NetworkResponse)
def get_network(
    disease: Optional[str] = Query(
        default=None,
        description="Disease slug, name, or ontology id",
    ),
) -> NetworkResponse:
    slug = _require_disease(disease or data_store.default_disease_slug())
    return data_store.build_network(slug)
