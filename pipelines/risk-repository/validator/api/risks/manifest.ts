import {
  type ProposedExtractionFields,
  REVIEW_MODES,
  type ReviewFields,
  type ReviewMode,
  type RiskEntry,
  type RiskFields,
  type RiskManifestResponse,
  type RiskOrigin,
} from "../../shared/classification.js";
import {
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
} from "../_airtable.js";
import { readAirtableEnv, type WorkerEnv } from "../_env.js";
import { parseEvidence } from "../_evidence.js";
import { errorResponse, handleError, queryParam } from "../_http.js";
import {
  fetchVisibleReviewsForPaper,
  indexReviewsByRisk,
  isPipelineReviewer,
  toReviewResponse,
  toReviewRow,
} from "../_reviews.js";
import { codableIds, parentId } from "../_tree.js";

const RISK_FETCH_FIELDS = [
  "ReadableId",
  "QuickRef",
  "Name",
  "Parent",
  "Description",
  "DescriptionPage",
  "SupportingQuote",
  "AdditionalEvidence",
  "Origin",
];

export default async function handler(
  request: Request,
  env: WorkerEnv,
): Promise<Response> {
  if (request.method !== "GET") {
    return errorResponse(405, "Method not allowed");
  }

  const params = new URL(request.url).searchParams;
  const quickRef = queryParam(params, "quickRef");
  const reviewer = queryParam(params, "reviewer");
  const mode = queryParam(params, "mode");

  if (quickRef === null) {
    return errorResponse(400, "quickRef query parameter is required");
  }
  if (reviewer === null) {
    return errorResponse(400, "reviewer query parameter is required");
  }
  if (mode === null || !isMode(mode)) {
    return errorResponse(
      400,
      'mode query parameter must be "blind" or "anchored"',
    );
  }

  try {
    const airtable = readAirtableEnv(env);
    const [risks, reviews, papers] = await Promise.all([
      listAllRecords<RiskFields>(
        airtable.pat,
        airtable.baseId,
        airtable.risksTable,
        {
          filterByFormula: `{QuickRef}="${escapeFormulaString(quickRef)}"`,
          fields: RISK_FETCH_FIELDS,
        },
      ),
      fetchVisibleReviewsForPaper(airtable, reviewer, quickRef, mode),
      listAllRecords<ProposedExtractionFields>(
        airtable.pat,
        airtable.baseId,
        airtable.proposedExtractionsTable,
        {
          filterByFormula: `{QuickRef}="${escapeFormulaString(quickRef)}"`,
          fields: ["Title"],
        },
      ),
    ]);

    const codable = codableIds(risks);
    const reviewsByRisk = indexReviewsByRisk(reviews);
    const entries = risks.map((risk) =>
      buildEntry(risk, codable, reviewsByRisk, reviewer, mode),
    );
    entries.sort((a, b) => a.readableId.localeCompare(b.readableId));

    const body: RiskManifestResponse = {
      quickRef,
      title: papers[0]?.fields.Title?.[0] ?? null,
      mode,
      risks: entries,
    };
    return Response.json(body);
  } catch (error) {
    return handleError(error);
  }
}

export function buildEntry(
  risk: AirtableRecord<RiskFields>,
  codable: Set<string>,
  reviewsByRisk: Map<string, AirtableRecord<ReviewFields>[]>,
  reviewer: string,
  mode: ReviewMode,
): RiskEntry {
  const riskReviews = (reviewsByRisk.get(risk.id) ?? []).map(toReviewRow);
  const responses = riskReviews
    .filter((row) => row.reviewer === reviewer)
    .map(toReviewResponse);
  const pipelineResponses =
    mode === "blind"
      ? []
      : riskReviews
          .filter((row) => isPipelineReviewer(row.reviewer))
          .map(toReviewResponse);

  return {
    id: risk.id,
    readableId: requiredField(risk, "ReadableId"),
    name: requiredField(risk, "Name"),
    parentId: parentId(risk),
    codable: codable.has(risk.id),
    origin: requiredOrigin(risk),
    description: risk.fields.Description ?? "",
    descriptionPage: risk.fields.DescriptionPage ?? null,
    supportingQuote: risk.fields.SupportingQuote ?? "",
    additionalEvidence: parseEvidence(risk.fields.AdditionalEvidence),
    responses,
    pipelineResponses,
  };
}

function requiredField(
  risk: AirtableRecord<RiskFields>,
  field: "ReadableId" | "Name",
): string {
  const value = risk.fields[field];
  if (value === undefined || value === "") {
    throw new Error(`Risk ${risk.id} is missing ${field}`);
  }
  return value;
}

function requiredOrigin(risk: AirtableRecord<RiskFields>): RiskOrigin {
  const origin = risk.fields.Origin;
  if (origin === undefined) {
    throw new Error(`Risk ${risk.id} is missing Origin`);
  }
  return origin;
}

function isMode(value: string): value is ReviewMode {
  return (REVIEW_MODES as readonly string[]).includes(value);
}
