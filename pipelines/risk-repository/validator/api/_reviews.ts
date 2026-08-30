import {
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
  listAllRecordsSharded,
  type ShardKey,
} from "@api/_airtable";
import type { AirtableEnv } from "@api/_env";
import {
  PIPELINE_REVIEWER_PREFIX,
  type ReviewField,
  type ReviewFields,
  type ReviewMode,
  type ReviewResponse,
} from "@shared/classification";

const REVIEW_FETCH_FIELDS = [
  "Risk",
  "Reviewer",
  "Field",
  "Value",
  "Mode",
  "Comment",
];

const RISK_READABLE_ID_LOOKUP = "ReadableId (from Risk)";

const ALL_PAPERS_SHARD: ShardKey = { field: "RiskReviewId", count: 4 };

export function isPipelineReviewer(reviewer: string): boolean {
  return reviewer.startsWith(PIPELINE_REVIEWER_PREFIX);
}

const PIPELINE_REVIEWER = `LEFT({Reviewer}, ${PIPELINE_REVIEWER_PREFIX.length})="${PIPELINE_REVIEWER_PREFIX}"`;

function ownReviewer(reviewer: string): string {
  return `{Reviewer}="${escapeFormulaString(reviewer)}"`;
}

function ownAndPipeline(reviewer: string): string {
  return `OR(${ownReviewer(reviewer)}, ${PIPELINE_REVIEWER})`;
}

export function paperScopeFormula(quickRef: string): string {
  // A risk's ReadableId is `{QuickRef}.NN.NN...`, so the paper's rows are the ones
  // whose linked risk carries that prefix. The trailing dot is load-bearing: some
  // QuickRefs are prefixes of others, and without it Lee2025 would match Lee2025a.
  const prefix = `${quickRef}.`;
  return `LEFT(ARRAYJOIN({${RISK_READABLE_ID_LOOKUP}}), ${prefix.length})="${escapeFormulaString(prefix)}"`;
}

export function reviewerScopeFormula(
  reviewer: string,
  mode: ReviewMode,
): string {
  return mode === "blind" ? ownReviewer(reviewer) : ownAndPipeline(reviewer);
}

// One human's rows plus the pipeline's, across every paper
export async function fetchVisibleReviews(
  airtable: AirtableEnv,
  reviewer: string,
): Promise<AirtableRecord<ReviewFields>[]> {
  return await listAllRecordsSharded<ReviewFields>(
    airtable.pat,
    airtable.baseId,
    airtable.reviewsTable,
    {
      filterByFormula: ownAndPipeline(reviewer),
      fields: REVIEW_FETCH_FIELDS,
    },
    ALL_PAPERS_SHARD,
  );
}

export async function fetchVisibleReviewsForPaper(
  airtable: AirtableEnv,
  reviewer: string,
  quickRef: string,
  mode: ReviewMode,
): Promise<AirtableRecord<ReviewFields>[]> {
  const paperScope = paperScopeFormula(quickRef);
  const reviewers = reviewerScopeFormula(reviewer, mode);
  return await listAllRecords<ReviewFields>(
    airtable.pat,
    airtable.baseId,
    airtable.reviewsTable,
    {
      filterByFormula: `AND(${paperScope}, ${reviewers})`,
      fields: REVIEW_FETCH_FIELDS,
    },
  );
}

export function requiredRiskId(review: AirtableRecord<ReviewFields>): string {
  const risk = review.fields.Risk;
  if (risk === undefined || risk.length === 0) {
    throw new Error(`Review ${review.id} is not linked to a risk`);
  }
  return risk[0];
}

export function indexReviewsByRisk(
  reviews: AirtableRecord<ReviewFields>[],
): Map<string, AirtableRecord<ReviewFields>[]> {
  const result = new Map<string, AirtableRecord<ReviewFields>[]>();
  for (const review of reviews) {
    const riskId = requiredRiskId(review);
    const list = result.get(riskId);
    if (list === undefined) {
      result.set(riskId, [review]);
    } else {
      list.push(review);
    }
  }
  return result;
}

export interface ReviewRow {
  id: string;
  reviewer: string;
  field: ReviewField;
  value: string;
  mode: ReviewMode;
  comment: string | null;
}

export function toReviewRow(record: AirtableRecord<ReviewFields>): ReviewRow {
  const { Reviewer, Field, Value, Mode } = record.fields;
  if (
    Reviewer === undefined ||
    Field === undefined ||
    Value === undefined ||
    Mode === undefined
  ) {
    throw new Error(
      `Review ${record.id} is missing Reviewer, Field, Value, or Mode`,
    );
  }
  return {
    id: record.id,
    reviewer: Reviewer,
    field: Field,
    value: Value,
    mode: Mode,
    comment: record.fields.Comment ?? null,
  };
}

export function toReviewResponse(row: ReviewRow): ReviewResponse {
  return {
    id: row.id,
    field: row.field,
    value: row.value,
    mode: row.mode,
    comment: row.comment,
  };
}
