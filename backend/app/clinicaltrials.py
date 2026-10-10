"""ClinicalTrials.gov API v2 client (small-scale, paginated)."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_URL = "https://clinicaltrials.gov/api/v2/studies"

FIELDS = ",".join(
    [
        "NCTId",
        "BriefTitle",
        "OverallStatus",
        "Phase",
        "StartDate",
        "CompletionDate",
        "WhyStopped",
        "InterventionName",
        "InterventionType",
        "Condition",
    ]
)


def _get_with_retry(
    client: httpx.Client,
    url: str,
    params: Dict[str, Any],
    retries: int = 5,
) -> Dict[str, Any]:
    last_error: Optional[Exception] = None
    for attempt in range(retries):
        response = client.get(url, params=params)
        if response.status_code == 429:
            wait = 1.5 * (2**attempt)
            time.sleep(wait)
            last_error = httpx.HTTPStatusError(
                "429", request=response.request, response=response
            )
            continue
        response.raise_for_status()
        return response.json()
    if last_error:
        raise last_error
    raise RuntimeError("ClinicalTrials.gov request failed")


def _fetch_pages(
    client: httpx.Client,
    url: str,
    base_params: Dict[str, Any],
    max_studies: int,
    delay_sec: float,
) -> List[Dict[str, Any]]:
    studies: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    while len(studies) < max_studies:
        params = dict(base_params)
        params["pageSize"] = min(
            int(base_params.get("pageSize", 100)), max_studies - len(studies)
        )
        if page_token:
            params["pageToken"] = page_token
        body = _get_with_retry(client, url, params)
        batch = body.get("studies") or []
        studies.extend(batch)
        page_token = body.get("nextPageToken")
        if not page_token or not batch:
            break
        time.sleep(delay_sec)
    return studies


def fetch_studies(
    condition: str = "asthma",
    page_size: int = 100,
    max_studies: int = 150,
    url: str = DEFAULT_URL,
    delay_sec: float = 0.35,
    timeout: float = 60.0,
    extra_interventions: Optional[List[str]] = None,
    max_per_intervention: int = 20,
) -> Dict[str, Any]:
    """Fetch condition studies plus optional intervention-targeted pulls; dedupe by NCT."""
    by_nct: Dict[str, Dict[str, Any]] = {}
    queries: List[Dict[str, Any]] = []

    with httpx.Client(timeout=timeout) as client:
        cond_params = {
            "query.cond": condition,
            "pageSize": page_size,
            "fields": FIELDS,
        }
        cond_studies = _fetch_pages(
            client, url, cond_params, max_studies, delay_sec
        )
        queries.append(
            {"type": "condition", "value": condition, "count": len(cond_studies)}
        )
        for study in cond_studies:
            nct = (
                ((study.get("protocolSection") or {}).get("identificationModule") or {}).get(
                    "nctId"
                )
            )
            if nct:
                by_nct[nct] = study

        for drug in extra_interventions or []:
            time.sleep(0.6)
            params = {
                "query.cond": condition,
                "query.intr": drug,
                "pageSize": min(page_size, max_per_intervention),
                "fields": FIELDS,
            }
            try:
                batch = _fetch_pages(
                    client, url, params, max_per_intervention, delay_sec
                )
            except Exception as exc:  # noqa: BLE001 — keep partial cache on rate limits
                queries.append(
                    {
                        "type": "intervention",
                        "value": drug,
                        "count": 0,
                        "error": str(exc),
                    }
                )
                continue
            queries.append({"type": "intervention", "value": drug, "count": len(batch)})
            for study in batch:
                nct = (
                    ((study.get("protocolSection") or {}).get("identificationModule") or {}).get(
                        "nctId"
                    )
                )
                if nct:
                    by_nct[nct] = study

    studies = list(by_nct.values())
    return {
        "query": {
            "source": "clinicaltrials_gov_v2",
            "url": url,
            "condition": condition,
            "fields": FIELDS,
            "max_studies": max_studies,
            "extra_interventions": extra_interventions or [],
            "subqueries": queries,
        },
        "count": len(studies),
        "studies": studies,
    }
