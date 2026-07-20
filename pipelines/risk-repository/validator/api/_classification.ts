// Classification-review contract shared between the frontend and the API routes.
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

export const VALIDITIES = ["ok", "not-a-risk"] as const;
export type Validity = (typeof VALIDITIES)[number];

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
  validity: VALIDITIES,
  entity: ENTITIES,
  intent: INTENTS,
  timing: TIMINGS,
  subdomain: SUBDOMAINS,
};

export const REVIEW_MODES = ["blind", "anchored"] as const;
export type ReviewMode = (typeof REVIEW_MODES)[number];

export const PIPELINE_REVIEWER_PREFIX = "pipeline:";

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
  extractionRun: string;
  documentTitle: string | null;
  description: string;
  supportingQuote: string;
  authorCategory: string | null;
  authorSubcategory: string | null;
  responses: ReviewResponse[];
  pipelineResponses: ReviewResponse[];
}

export interface RiskManifestResponse {
  extractionRun: string;
  mode: ReviewMode;
  risks: RiskEntry[];
}

export interface ExtractionRunInfo {
  extractionRun: string;
  riskCount: number;
  pipelineReviewers: string[];
}

export interface RunsResponse {
  runs: ExtractionRunInfo[];
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

export interface RiskFields {
  ExtractionRun?: string;
  ReadableId?: string;
  DocumentTitle?: string;
  Description?: string;
  SupportingQuote?: string;
  AuthorCategory?: string;
  AuthorSubcategory?: string;
}

export interface ReviewFields {
  Risk?: string[];
  Reviewer?: string;
  Field?: ReviewField;
  Value?: string;
  Mode?: ReviewMode;
  Comment?: string;
}
