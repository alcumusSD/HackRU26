import type {
  ChatMessage,
  ChatResponse,
  DiseaseInfo,
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

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

function withDisease(path: string, disease?: string): string {
  if (!disease) return path;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}disease=${encodeURIComponent(disease)}`;
}

export function fetchDiseases(): Promise<DiseaseInfo[]> {
  return getJson<DiseaseInfo[]>("/diseases");
}

export function fetchGenes(disease = "asthma"): Promise<GeneListResponse> {
  return getJson<GeneListResponse>(
    `/genes?disease=${encodeURIComponent(disease)}`,
  );
}

export function fetchGene(id: string, disease?: string): Promise<Gene> {
  return getJson<Gene>(
    withDisease(`/genes/${encodeURIComponent(id)}`, disease),
  );
}

export function fetchTrials(id: string, disease?: string): Promise<Trial[]> {
  return getJson<Trial[]>(
    withDisease(`/genes/${encodeURIComponent(id)}/trials`, disease),
  );
}

export function fetchJudgment(
  id: string,
  disease?: string,
): Promise<JudgmentCard> {
  return getJson<JudgmentCard>(
    withDisease(`/genes/${encodeURIComponent(id)}/judgment`, disease),
  );
}

export function fetchNetwork(disease = "asthma"): Promise<NetworkResponse> {
  return getJson<NetworkResponse>(
    `/network?disease=${encodeURIComponent(disease)}`,
  );
}

export function postChat(payload: {
  message: string;
  context: Record<string, unknown>;
  history: ChatMessage[];
}): Promise<ChatResponse> {
  return postJson<ChatResponse>("/chat", payload);
}

export { API_URL };
