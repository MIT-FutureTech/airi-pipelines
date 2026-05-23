import type {
  DecisionRequest,
  DecisionResponse,
  ManifestResponse,
} from "@api/_shared";

const manifestCache = new Map<string, Promise<ManifestResponse>>();

async function fetchJson<T>(url: string, label: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to load ${label}: HTTP ${response.status} ${body}`);
  }
  return (await response.json()) as T;
}

export function getManifest(reviewer: string): Promise<ManifestResponse> {
  let promise = manifestCache.get(reviewer);
  if (promise === undefined) {
    promise = fetchJson<ManifestResponse>(
      `/api/documents/manifest?reviewer=${encodeURIComponent(reviewer)}`,
      "manifest",
    );
    manifestCache.set(reviewer, promise);
  }
  return promise;
}

export async function submitDecision(
  body: DecisionRequest,
): Promise<DecisionResponse> {
  const response = await fetch("/api/decisions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(
      `Failed to submit decision: HTTP ${response.status} ${text}`,
    );
  }
  return (await response.json()) as DecisionResponse;
}
