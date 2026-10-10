"""Small-scale Open Targets GraphQL client (one disease)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

DEFAULT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

DISEASE_TARGETS_QUERY = """
query DiseaseTargets($diseaseId: String!, $limit: Int!) {
  disease(efoId: $diseaseId) {
    id
    name
    associatedTargets(page: { index: 0, size: $limit }) {
      count
      rows {
        score
        target {
          id
          approvedSymbol
          approvedName
        }
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""


def fetch_disease_targets(
    disease_id: str,
    limit: int = 15,
    url: str = DEFAULT_URL,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """POST GraphQL and return the full JSON body (includes data/errors)."""
    payload = {
        "query": DISEASE_TARGETS_QUERY,
        "variables": {"diseaseId": disease_id, "limit": limit},
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        body = response.json()

    if body.get("errors"):
        raise RuntimeError(f"Open Targets GraphQL errors: {body['errors']}")

    disease = (body.get("data") or {}).get("disease")
    if disease is None:
        raise RuntimeError(
            f"Disease '{disease_id}' not found in Open Targets. "
            "Try searching the platform for the current ontology ID."
        )
    return body


def datatype_score(row: Dict[str, Any], datatype_id: str) -> Optional[float]:
    for item in row.get("datatypeScores") or []:
        if item.get("id") == datatype_id and item.get("score") is not None:
            return float(item["score"])
    return None
