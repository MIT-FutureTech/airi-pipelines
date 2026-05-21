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
  decision: Decision | null;
  comments: string | null;
  validationId: string | null;
}

export interface ManifestResponse {
  documents: ManifestEntry[];
}

export interface DocumentDetail {
  id: string;
  readableId: string;
  title: string | null;
  abstract: string | null;
}

export interface DecisionRequest {
  reviewer: string;
  documentId: string;
  validationId: string | null;
  decision: Decision;
  comments: string | null;
}

export interface DecisionResponse {
  documentId: string;
  validationId: string;
  decision: Decision;
  comments: string | null;
}
