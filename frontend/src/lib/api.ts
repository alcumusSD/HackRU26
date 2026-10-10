import type {
  Gene,
  GeneListResponse,
  JudgmentCard,
  NetworkResponse,
  Trial,
} from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchGenes(disease = "asthma"): Promise<GeneListResponse> {
  return getJson<GeneListResponse>(
    `/genes?disease=${encodeURIComponent(disease)}`,
  );
}

export function fetchGene(id: string): Promise<Gene> {
  return getJson<Gene>(`/genes/${encodeURIComponent(id)}`);
}

export function fetchTrials(id: string): Promise<Trial[]> {
  return getJson<Trial[]>(`/genes/${encodeURIComponent(id)}/trials`);
}

export function fetchJudgment(id: string): Promise<JudgmentCard> {
  return getJson<JudgmentCard>(`/genes/${encodeURIComponent(id)}/judgment`);
}

export function fetchNetwork(disease = "asthma"): Promise<NetworkResponse> {
  return getJson<NetworkResponse>(
    `/network?disease=${encodeURIComponent(disease)}`,
  );
}

export { API_URL };
