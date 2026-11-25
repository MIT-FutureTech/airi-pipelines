import type {
  Judgement,
  JudgementsResponse,
  SaveJudgementRequest,
} from "@shared/judgements";
import type { Bundle } from "@/lib/types";

const BUNDLE_PATH = "/data/bundle.json";
const JUDGEMENTS_PATH = "/api/judgements";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(
      `Failed to load ${path}: HTTP ${response.status} ${await response.text()}`,
    );
  }
  return (await response.json()) as T;
}

let bundle: Promise<Bundle> | undefined;

export function getBundle(): Promise<Bundle> {
  bundle ??= fetchJson<Bundle>(BUNDLE_PATH);
  return bundle;
}

let judgements: Promise<JudgementsResponse> | undefined;

export function getJudgements(): Promise<JudgementsResponse> {
  judgements ??= fetchJson<JudgementsResponse>(JUDGEMENTS_PATH);
  return judgements;
}

export async function saveJudgement(
  request: SaveJudgementRequest,
): Promise<Judgement> {
  const response = await fetch(JUDGEMENTS_PATH, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(
      `Failed to save judgement: HTTP ${response.status} ${await response.text()}`,
    );
  }
  return (await response.json()) as Judgement;
}
