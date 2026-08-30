import {
  type PapersResponse,
  type PdfLinkResponse,
  REVIEW_MODES,
  type ReviewMode,
  type RiskManifestResponse,
  type SaveCodingsRequest,
  type SaveCodingsResponse,
} from "@shared/classification";
import { isCoded } from "@shared/coding";
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
        `was ${contentType}. Set VITE_API_PROXY_TARGET to use a ` +
        "deployed API.",
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

// Writes replace this cache's entries, so callers must hold the promise they
// get in state.
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

function applySavedCodings(
  quickRef: string,
  reviewer: string,
  saved: SaveCodingsResponse,
): void {
  const manifest = patchRiskManifests(quickRef, reviewer, saved);
  if (manifest === null) {
    papersCache.delete(papersUrl(reviewer));
    return;
  }
  patchPaperProgress(quickRef, reviewer, manifest);
}

function patchRiskManifests(
  quickRef: string,
  reviewer: string,
  saved: SaveCodingsResponse,
): Promise<RiskManifestResponse> | null {
  let patched: Promise<RiskManifestResponse> | null = null;
  for (const mode of REVIEW_MODES) {
    const url = riskManifestUrl({ quickRef, reviewer, mode });
    const cached = riskManifestCache.get(url);
    if (cached === undefined) {
      continue;
    }
    patched = cached.then((manifest) => ({
      ...manifest,
      risks: manifest.risks.map((risk) =>
        risk.id === saved.riskId
          ? { ...risk, responses: saved.responses }
          : risk,
      ),
    }));
    riskManifestCache.set(url, patched);
  }
  return patched;
}

function patchPaperProgress(
  quickRef: string,
  reviewer: string,
  manifest: Promise<RiskManifestResponse>,
): void {
  const url = papersUrl(reviewer);
  const cached = papersCache.get(url);
  if (cached === undefined) {
    return;
  }
  papersCache.set(
    url,
    Promise.all([cached, manifest]).then(
      ([papers, risks]) => ({
        papers: papers.papers.map((paper) =>
          paper.quickRef === quickRef
            ? { ...paper, reviewerCodedCount: codedRiskCount(risks) }
            : paper,
        ),
      }),
      () => cached,
    ),
  );
}

function codedRiskCount(manifest: RiskManifestResponse): number {
  return manifest.risks.filter(
    (risk) => risk.codable && isCoded(risk.responses),
  ).length;
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
  quickRef: string,
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
  const saved = (await response.json()) as SaveCodingsResponse;
  applySavedCodings(quickRef, body.reviewer, saved);
  return saved;
}
