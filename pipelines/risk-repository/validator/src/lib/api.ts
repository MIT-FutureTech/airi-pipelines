import type {
  DecisionRequest,
  DecisionResponse,
  DocumentDetail,
  ManifestResponse,
} from "@api/_shared";

const cache = new Map<string, Promise<unknown>>();

function memoized<T>(key: string, factory: () => Promise<T>): Promise<T> {
  let promise = cache.get(key);
  if (promise === undefined) {
    promise = factory();
    cache.set(key, promise);
  }
  return promise as Promise<T>;
}

async function fetchJson<T>(url: string, label: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to load ${label}: HTTP ${response.status} ${body}`);
  }
  return (await response.json()) as T;
}

export function getManifest(reviewer: string): Promise<ManifestResponse> {
  const key = `manifest:${reviewer}`;
  return memoized(key, () =>
    fetchJson<ManifestResponse>(
      `/api/documents/manifest?reviewer=${encodeURIComponent(reviewer)}`,
      "manifest",
    ),
  );
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return memoized(`document:${id}`, () =>
    fetchJson<DocumentDetail>(`/api/documents/${id}`, `document ${id}`),
  );
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
