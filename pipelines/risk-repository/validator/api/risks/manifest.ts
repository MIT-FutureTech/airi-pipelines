import type { VercelRequest, VercelResponse } from "@vercel/node";
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
import { readAirtableEnv } from "../_env.js";
import { parseEvidence } from "../_evidence.js";
import { handleError, queryString } from "../_http.js";
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
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const quickRef = queryString(req.query.quickRef);
  const reviewer = queryString(req.query.reviewer);
  const mode = queryString(req.query.mode);

  if (quickRef === null) {
    res.status(400).json({ error: "quickRef query parameter is required" });
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

  try {
    const env = readAirtableEnv();
    const [risks, reviews, papers] = await Promise.all([
      listAllRecords<RiskFields>(env.pat, env.baseId, env.risksTable, {
        filterByFormula: `{QuickRef}="${escapeFormulaString(quickRef)}"`,
        fields: RISK_FETCH_FIELDS,
      }),
      fetchVisibleReviewsForPaper(env, reviewer, quickRef, mode),
      listAllRecords<ProposedExtractionFields>(
        env.pat,
        env.baseId,
        env.proposedExtractionsTable,
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
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
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
