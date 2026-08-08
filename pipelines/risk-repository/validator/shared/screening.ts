export type Stage = "abstract" | "full text";
export type Decision = "include" | "exclude" | "uncertain";

export const DECISIONS: readonly Decision[] = [
  "include",
  "exclude",
  "uncertain",
];

export interface ManifestEntry {
  id: string;
  readableId: string;
  title: string | null;
  abstract: string | null;
  decision: Decision | null;
  comments: string | null;
  decisionId: string | null;
}

export interface ManifestResponse {
  documents: ManifestEntry[];
}

export interface DecisionRequest {
  reviewer: string;
  documentId: string;
  decisionId: string | null;
  decision: Decision;
  comments: string | null;
}

export interface DecisionResponse {
  documentId: string;
  decisionId: string;
  decision: Decision;
  comments: string | null;
}
