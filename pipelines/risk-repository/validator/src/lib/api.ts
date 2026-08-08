import type {
  PapersResponse,
  ReviewMode,
  ReviewUpsertRequest,
  ReviewUpsertResponse,
  RiskManifestResponse,
} from "@shared/classification";
import type {
  DecisionRequest,
  DecisionResponse,
  ManifestResponse,
} from "@shared/screening";

const manifestCache = new Map<string, Promise<ManifestResponse>>();

async function fetchJson<T>(url: string, label: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Failed to load ${label}: HTTP ${response.status} ${body}`);
  }
  // `vite` alone serves index.html for /api/*, so a non-JSON 200 here means the
  // serverless functions are not running.
  const contentType = response.headers.get("content-type") ?? "none";
  if (!contentType.includes("application/json")) {
    throw new Error(
      `Failed to load ${label}: expected JSON from ${url} but the content type ` +
        `was ${contentType}. Run \`npm run dev:vercel\`, or set ` +
        "VITE_API_PROXY_TARGET to use a deployed API.",
    );
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

export interface RiskManifestParams {
  quickRef: string;
  reviewer: string;
  mode: ReviewMode;
}

const papersCache = new Map<string, Promise<PapersResponse>>();

function papersUrl(reviewer: string): string {
  return `/api/papers?reviewer=${encodeURIComponent(reviewer)}`;
}

export function getPapers(reviewer: string): Promise<PapersResponse> {
  const url = papersUrl(reviewer);
  let promise = papersCache.get(url);
  if (promise === undefined) {
    promise = fetchJson<PapersResponse>(url, "papers");
    papersCache.set(url, promise);
  }
  return promise;
}

const riskManifestCache = new Map<string, Promise<RiskManifestResponse>>();

function riskManifestUrl(params: RiskManifestParams): string {
  const query = new URLSearchParams({
    quickRef: params.quickRef,
    reviewer: params.reviewer,
    mode: params.mode,
  });
  return `/api/risks/manifest?${query.toString()}`;
}

// Cached because `use()` needs a promise whose identity is stable across
// renders. `useMemo` cannot supply one: React may discard a memo and recompute,
// which would suspend on a fresh promise every time.
export function getRiskManifest(
  params: RiskManifestParams,
): Promise<RiskManifestResponse> {
  const url = riskManifestUrl(params);
  let promise = riskManifestCache.get(url);
  if (promise === undefined) {
    promise = fetchJson<RiskManifestResponse>(url, "risk manifest");
    riskManifestCache.set(url, promise);
  }
  return promise;
}

export async function fetchRiskManifest(
  params: RiskManifestParams,
): Promise<RiskManifestResponse> {
  const url = riskManifestUrl(params);
  const fresh = fetchJson<RiskManifestResponse>(url, "risk manifest");
  riskManifestCache.set(url, fresh);
  return await fresh;
}

function invalidateClassificationCaches(): void {
  riskManifestCache.clear();
  papersCache.clear();
}

export async function submitReview(
  body: ReviewUpsertRequest,
): Promise<ReviewUpsertResponse> {
  const response = await fetch("/api/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to submit review: HTTP ${response.status} ${text}`);
  }
  invalidateClassificationCaches();
  return (await response.json()) as ReviewUpsertResponse;
}

export async function deleteReview(reviewId: string): Promise<void> {
  const response = await fetch(
    `/api/reviews?reviewId=${encodeURIComponent(reviewId)}`,
    { method: "DELETE" },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to delete review: HTTP ${response.status} ${text}`);
  }
  invalidateClassificationCaches();
}
