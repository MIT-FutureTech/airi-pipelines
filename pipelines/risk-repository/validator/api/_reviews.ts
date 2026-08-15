import {
  PIPELINE_REVIEWER_PREFIX,
  type ReviewFields,
  type ReviewMode,
  type ReviewResponse,
} from "../shared/classification.js";
import {
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
  listAllRecordsSharded,
  type ShardKey,
} from "./_airtable.js";
import type { AirtableEnv } from "./_env.js";

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

// One human's rows plus the pipeline's, across every paper
export async function fetchVisibleReviews(
  env: AirtableEnv,
  reviewer: string,
): Promise<AirtableRecord<ReviewFields>[]> {
  return await listAllRecordsSharded<ReviewFields>(
    env.pat,
    env.baseId,
    env.reviewsTable,
    {
      filterByFormula: ownAndPipeline(reviewer),
      fields: REVIEW_FETCH_FIELDS,
    },
    ALL_PAPERS_SHARD,
  );
}

export async function fetchVisibleReviewsForPaper(
  env: AirtableEnv,
  reviewer: string,
  quickRef: string,
  mode: ReviewMode,
): Promise<AirtableRecord<ReviewFields>[]> {
  // A risk's ReadableId is `{QuickRef}.NN.NN...`, so the paper's rows are the ones
  // whose linked risk carries that prefix. The trailing dot is load-bearing: some
  // QuickRefs are prefixes of others, and without it Lee2025 would match Lee2025a.
  const prefix = `${quickRef}.`;
  const paperScope = `LEFT(ARRAYJOIN({${RISK_READABLE_ID_LOOKUP}}), ${prefix.length})="${escapeFormulaString(prefix)}"`;
  const reviewers =
    mode === "blind" ? ownReviewer(reviewer) : ownAndPipeline(reviewer);
  return await listAllRecords<ReviewFields>(
    env.pat,
    env.baseId,
    env.reviewsTable,
    {
      filterByFormula: `AND(${paperScope}, ${reviewers})`,
      fields: REVIEW_FETCH_FIELDS,
    },
  );
}

export function indexReviewsByRisk(
  reviews: AirtableRecord<ReviewFields>[],
): Map<string, AirtableRecord<ReviewFields>[]> {
  const result = new Map<string, AirtableRecord<ReviewFields>[]>();
  for (const review of reviews) {
    const risk = review.fields.Risk;
    if (risk === undefined || risk.length === 0) {
      console.warn(`Skipping review ${review.id}: not linked to a risk`);
      continue;
    }
    const list = result.get(risk[0]);
    if (list === undefined) {
      result.set(risk[0], [review]);
    } else {
      list.push(review);
    }
  }
  return result;
}

export function toReviewResponse(
  record: AirtableRecord<ReviewFields>,
): ReviewResponse {
  const { Field, Value, Mode } = record.fields;
  if (Field === undefined || Value === undefined || Mode === undefined) {
    throw new Error(`Review ${record.id} is missing Field, Value, or Mode`);
  }
  return {
    id: record.id,
    field: Field,
    value: Value,
    mode: Mode,
    comment: record.fields.Comment ?? null,
  };
}
