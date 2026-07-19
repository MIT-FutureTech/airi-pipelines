import type { VercelRequest, VercelResponse } from "@vercel/node";
import {
  AirtableError,
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
} from "../_airtable.js";
import {
  REVIEW_MODES,
  type ReviewFields,
  type ReviewMode,
  type ReviewResponse,
  type RiskEntry,
  type RiskFields,
  type RiskManifestResponse,
} from "../_classification.js";
import { readAirtableEnv } from "../_env.js";

const RISK_FETCH_FIELDS = [
  "ExtractionRun",
  "ReadableId",
  "DocumentTitle",
  "Description",
  "SupportingQuote",
  "AuthorCategory",
  "AuthorSubcategory",
];

const REVIEW_FETCH_FIELDS = [
  "Risk",
  "Reviewer",
  "Field",
  "Value",
  "Mode",
  "Comment",
];

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const extractionRun = queryString(req.query.extractionRun);
  const reviewer = queryString(req.query.reviewer);
  const mode = queryString(req.query.mode);
  const pipelineReviewer = queryString(req.query.pipelineReviewer);

  if (extractionRun === null) {
    res
      .status(400)
      .json({ error: "extractionRun query parameter is required" });
    return;
  }
  if (reviewer === null) {
    res.status(400).json({ error: "reviewer query parameter is required" });
    return;
  }
  if (mode === null || !isMode(mode)) {
    res
      .status(400)
      .json({ error: 'mode query parameter must be "blind" or "anchored"' });
    return;
  }
  if (mode === "anchored" && pipelineReviewer === null) {
    res.status(400).json({
      error: "pipelineReviewer query parameter is required in anchored mode",
    });
    return;
  }

  try {
    const env = readAirtableEnv();
    const anchorReviewer = mode === "anchored" ? pipelineReviewer : null;
    const reviewers =
      anchorReviewer === null ? [reviewer] : [reviewer, anchorReviewer];
    const [risks, reviews] = await Promise.all([
      listAllRecords<RiskFields>(env.pat, env.baseId, env.risksTable, {
        filterByFormula: `{ExtractionRun}="${escapeFormulaString(extractionRun)}"`,
        fields: RISK_FETCH_FIELDS,
      }),
      listAllRecords<ReviewFields>(env.pat, env.baseId, env.reviewsTable, {
        filterByFormula: reviewerFormula(reviewers),
        fields: REVIEW_FETCH_FIELDS,
      }),
    ]);

    const reviewsByRisk = indexReviewsByRisk(reviews);
    const entries = risks.map((risk) =>
      buildEntry(risk, reviewsByRisk, reviewer, anchorReviewer),
    );
    entries.sort((a, b) => a.readableId.localeCompare(b.readableId));

    const body: RiskManifestResponse = { extractionRun, mode, risks: entries };
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
  }
}

function buildEntry(
  risk: AirtableRecord<RiskFields>,
  reviewsByRisk: Map<string, AirtableRecord<ReviewFields>[]>,
  reviewer: string,
  anchorReviewer: string | null,
): RiskEntry {
  const riskReviews = reviewsByRisk.get(risk.id) ?? [];
  const responses = riskReviews
    .filter((review) => review.fields.Reviewer === reviewer)
    .map(toReviewResponse);
  const pipelineResponses =
    anchorReviewer === null
      ? []
      : riskReviews
          .filter((review) => review.fields.Reviewer === anchorReviewer)
          .map(toReviewResponse);
  return {
    id: risk.id,
    readableId: requiredField(risk, "ReadableId"),
    extractionRun: requiredField(risk, "ExtractionRun"),
    documentTitle: risk.fields.DocumentTitle ?? null,
    description: requiredField(risk, "Description"),
    supportingQuote: requiredField(risk, "SupportingQuote"),
    authorCategory: risk.fields.AuthorCategory ?? null,
    authorSubcategory: risk.fields.AuthorSubcategory ?? null,
    responses,
    pipelineResponses,
  };
}

function toReviewResponse(
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

function indexReviewsByRisk(
  reviews: AirtableRecord<ReviewFields>[],
): Map<string, AirtableRecord<ReviewFields>[]> {
  const result = new Map<string, AirtableRecord<ReviewFields>[]>();
  for (const review of reviews) {
    const risk = review.fields.Risk;
    if (risk === undefined || risk.length === 0) {
      throw new Error(`Review ${review.id} is not linked to a risk`);
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

function requiredField(
  risk: AirtableRecord<RiskFields>,
  field: keyof RiskFields,
): string {
  const value = risk.fields[field];
  if (typeof value !== "string" || value === "") {
    throw new Error(`Risk ${risk.id} is missing ${field}`);
  }
  return value;
}

function reviewerFormula(reviewers: string[]): string {
  const clauses = reviewers.map(
    (reviewer) => `{Reviewer}="${escapeFormulaString(reviewer)}"`,
  );
  if (clauses.length === 1) {
    return clauses[0];
  }
  return `OR(${clauses.join(",")})`;
}

function isMode(value: string): value is ReviewMode {
  return (REVIEW_MODES as readonly string[]).includes(value);
}

function queryString(value: string | string[] | undefined): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function handleError(res: VercelResponse, error: unknown): void {
  if (error instanceof AirtableError) {
    res
      .status(502)
      .json({ error: "Airtable request failed", detail: error.body });
    return;
  }
  const message = error instanceof Error ? error.message : String(error);
  res.status(500).json({ error: message });
}
