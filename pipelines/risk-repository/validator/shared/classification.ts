// Taxonomy value domains mirror
// pipelines/risk-repository/src/risk_repository/classify.py.

export const ENTITIES = ["human", "ai", "other"] as const;
export type Entity = (typeof ENTITIES)[number];

export const INTENTS = ["intentional", "unintentional", "other"] as const;
export type Intent = (typeof INTENTS)[number];

export const TIMINGS = ["pre-deployment", "post-deployment", "other"] as const;
export type Timing = (typeof TIMINGS)[number];

export const SUBDOMAINS = [
  "1.1",
  "1.2",
  "1.3",
  "2.1",
  "2.2",
  "3.1",
  "3.2",
  "4.1",
  "4.2",
  "4.3",
  "5.1",
  "5.2",
  "6.1",
  "6.2",
  "6.3",
  "6.4",
  "6.5",
  "6.6",
  "7.1",
  "7.2",
  "7.3",
  "7.4",
  "7.5",
  "7.6",
  "X.1",
] as const;
export type Subdomain = (typeof SUBDOMAINS)[number];

export const NOT_A_RISK = "not-a-risk";

export const REVIEW_FIELDS = [
  "validity",
  "entity",
  "intent",
  "timing",
  "subdomain",
] as const;
export type ReviewField = (typeof REVIEW_FIELDS)[number];

export const AXIS_FIELDS: readonly ReviewField[] = [
  "entity",
  "intent",
  "timing",
  "subdomain",
];

export const REVIEW_FIELD_VALUES: Record<ReviewField, readonly string[]> = {
  validity: [NOT_A_RISK],
  entity: ENTITIES,
  intent: INTENTS,
  timing: TIMINGS,
  subdomain: SUBDOMAINS,
};

export const REVIEW_MODES = ["blind", "anchored"] as const;
export type ReviewMode = (typeof REVIEW_MODES)[number];

export const PIPELINE_REVIEWER_PREFIX = "pipeline:";

export const RISK_ORIGINS = [
  "model-added, human-approved",
  "model-added, human-edited",
  "human-added",
  "model-added, human-rejected",
] as const;
export type RiskOrigin = (typeof RISK_ORIGINS)[number];

export const REJECTED_ORIGIN = "model-added, human-rejected";

export const CLASSIFICATION_PROGRESS_VALUES = [
  "Not Started",
  "In Progress",
  "Complete",
] as const;
export type ClassificationProgress =
  (typeof CLASSIFICATION_PROGRESS_VALUES)[number];

export const PAPER_STATES = [
  "awaiting-extraction",
  "classifying",
  "ready",
] as const;
export type PaperState = (typeof PAPER_STATES)[number];

export interface EvidenceField {
  key: string;
  value: string;
}

export interface EvidenceItem {
  index: number;
  fields: EvidenceField[];
}

export interface ReviewResponse {
  id: string;
  field: ReviewField;
  value: string;
  mode: ReviewMode;
  comment: string | null;
}

export interface RiskEntry {
  id: string;
  readableId: string;
  name: string;
  parentId: string | null;
  codable: boolean;
  origin: RiskOrigin;
  description: string;
  descriptionPage: number | null;
  supportingQuote: string;
  additionalEvidence: EvidenceItem[];
  responses: ReviewResponse[];
  pipelineResponses: ReviewResponse[];
}

export interface RiskManifestResponse {
  quickRef: string;
  title: string | null;
  mode: ReviewMode;
  risks: RiskEntry[];
}

export interface PaperEntry {
  quickRef: string;
  title: string | null;
  assignee: string | null;
  progress: ClassificationProgress | null;
  state: PaperState;
  codableCount: number;
  reviewerCodedCount: number;
  pipelineCodedCount: number;
}

export interface PapersResponse {
  papers: PaperEntry[];
}

export interface ReviewUpsertRequest {
  reviewer: string;
  riskId: string;
  reviewId: string | null;
  field: ReviewField;
  value: string;
  mode: ReviewMode;
  comment: string | null;
}

export interface ReviewUpsertResponse {
  riskId: string;
  reviewId: string;
  field: ReviewField;
  value: string;
}

export interface AirtableCollaborator {
  id: string;
  email?: string;
  name?: string;
}

export interface RiskFields {
  ReadableId?: string;
  QuickRef?: string;
  Name?: string;
  Parent?: string[];
  Children?: string[];
  Description?: string;
  DescriptionPage?: number;
  SupportingQuote?: string;
  AdditionalEvidence?: string;
  Reviewer?: string;
  Origin?: RiskOrigin;
  ExtractionRun?: string;
  ApprovedAt?: string;
}

export interface ReviewFields {
  Risk?: string[];
  Reviewer?: string;
  Field?: ReviewField;
  Value?: string;
  Mode?: ReviewMode;
  Comment?: string;
}

export interface ProposedExtractionFields {
  QuickRef?: string;
  Title?: string[];
  ClassificationReviewer?: AirtableCollaborator;
  ClassificationProgress?: ClassificationProgress;
}
