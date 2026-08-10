import type {
  PapersResponse,
  PdfLinkResponse,
  ReviewMode,
  RiskManifestResponse,
  SaveCodingsRequest,
  SaveCodingsResponse,
} from "@shared/classification";
import type {
  DecisionRequest,
  DecisionResponse,
  ManifestResponse,
} from "@shared/screening";

const manifestCache = new Map<string, Promise<ManifestResponse>>();

function encodeQuery(params: Record<string, string>): string {
  return Object.entries(params)
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join("&");
}

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
      `/api/documents/manifest?${encodeQuery({ reviewer })}`,
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
  return `/api/papers?${encodeQuery({ reviewer })}`;
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
  const query = encodeQuery({
    quickRef: params.quickRef,
    reviewer: params.reviewer,
    mode: params.mode,
  });
  return `/api/risks/manifest?${query}`;
}

// Writes clear this cache, so callers must hold the promise they get in state.
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

export async function fetchPdfLink(quickRef: string): Promise<PdfLinkResponse> {
  const response = await fetch(`/api/pdf?${encodeQuery({ quickRef })}`);
  if (response.status === 404) {
    throw new Error(`No PDF is attached to ${quickRef} in Airtable`);
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to find the PDF: HTTP ${response.status} ${text}`);
  }
  return (await response.json()) as PdfLinkResponse;
}

export async function saveCodings(
  body: SaveCodingsRequest,
): Promise<SaveCodingsResponse> {
  const response = await fetch("/api/codings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to save coding: HTTP ${response.status} ${text}`);
  }
  invalidateClassificationCaches();
  return (await response.json()) as SaveCodingsResponse;
}
