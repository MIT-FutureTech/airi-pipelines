import type {
  ReviewMode,
  ReviewUpsertRequest,
  ReviewUpsertResponse,
  RiskManifestResponse,
} from "@api/_classification";
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

export interface RiskManifestParams {
  extractionRun: string;
  reviewer: string;
  mode: ReviewMode;
  pipelineReviewer: string | null;
}

const riskManifestCache = new Map<string, Promise<RiskManifestResponse>>();

export function getRiskManifest(
  params: RiskManifestParams,
): Promise<RiskManifestResponse> {
  const query = new URLSearchParams({
    extractionRun: params.extractionRun,
    reviewer: params.reviewer,
    mode: params.mode,
  });
  if (params.pipelineReviewer !== null) {
    query.set("pipelineReviewer", params.pipelineReviewer);
  }
  const url = `/api/risks/manifest?${query.toString()}`;
  let promise = riskManifestCache.get(url);
  if (promise === undefined) {
    promise = fetchJson<RiskManifestResponse>(url, "risk manifest");
    riskManifestCache.set(url, promise);
  }
  return promise;
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
  return (await response.json()) as ReviewUpsertResponse;
}
