import type { VercelRequest, VercelResponse } from "@vercel/node";
import type {
  PaperEntry,
  PaperState,
  PapersResponse,
  ProposedExtractionFields,
  ReviewFields,
  RiskFields,
} from "../shared/classification.js";
import { type Coding, isCoded } from "../shared/coding.js";
import { type AirtableRecord, listAllRecords } from "./_airtable.js";
import { readAirtableEnv } from "./_env.js";
import { handleError, queryString } from "./_http.js";
import {
  fetchVisibleReviews,
  indexReviewsByRisk,
  isPipelineReviewer,
  type ReviewRow,
  toReviewRow,
} from "./_reviews.js";
import { codableIds } from "./_tree.js";

const PAPER_FETCH_FIELDS = [
  "QuickRef",
  "Title",
  "ClassificationReviewer",
  "ClassificationProgress",
];

const RISK_FETCH_FIELDS = ["QuickRef", "Parent", "Origin"];

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const reviewer = queryString(req.query.reviewer);
  if (reviewer === null) {
    res.status(400).json({ error: "reviewer query parameter is required" });
    return;
  }

  try {
    const env = readAirtableEnv();
    const [papers, risks, reviews] = await Promise.all([
      listAllRecords<ProposedExtractionFields>(
        env.pat,
        env.baseId,
        env.proposedExtractionsTable,
        { fields: PAPER_FETCH_FIELDS },
      ),
      listAllRecords<RiskFields>(env.pat, env.baseId, env.risksTable, {
        fields: RISK_FETCH_FIELDS,
      }),
      fetchVisibleReviews(env, reviewer),
    ]);

    const codable = codableIds(risks);
    const reviewsByRisk = indexReviewsByRisk(reviews);
    const risksByPaper = groupRisksByPaper(risks);

    const entries: PaperEntry[] = [];
    for (const paper of papers) {
      const quickRef = requiredQuickRef(paper);
      entries.push(
        buildEntry(
          quickRef,
          paper.fields,
          risksByPaper.get(quickRef) ?? [],
          codable,
          reviewsByRisk,
          reviewer,
        ),
      );
    }
    entries.sort((a, b) => a.quickRef.localeCompare(b.quickRef));

    const body: PapersResponse = { papers: entries };
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
  }
}

export function buildEntry(
  quickRef: string,
  fields: ProposedExtractionFields,
  risks: AirtableRecord<RiskFields>[],
  codable: Set<string>,
  reviewsByRisk: Map<string, AirtableRecord<ReviewFields>[]>,
  reviewer: string,
): PaperEntry {
  const codableRisks = risks.filter((risk) => codable.has(risk.id));

  let reviewerCodedCount = 0;
  let pipelineCodedCount = 0;
  for (const risk of codableRisks) {
    const rows = (reviewsByRisk.get(risk.id) ?? []).map(toReviewRow);
    if (isCoded(codingsBy(rows, (name) => name === reviewer))) {
      reviewerCodedCount += 1;
    }
    if (isCoded(codingsBy(rows, isPipelineReviewer))) {
      pipelineCodedCount += 1;
    }
  }

  return {
    quickRef,
    title: fields.Title?.[0] ?? null,
    assignee: fields.ClassificationReviewer?.name ?? null,
    progress: fields.ClassificationProgress ?? null,
    state: paperState(risks.length, codableRisks.length, pipelineCodedCount),
    codableCount: codableRisks.length,
    reviewerCodedCount,
    pipelineCodedCount,
  };
}

export function paperState(
  riskCount: number,
  codableCount: number,
  pipelineCodedCount: number,
): PaperState {
  if (riskCount === 0) {
    return "awaiting-extraction";
  }
  return pipelineCodedCount === codableCount ? "ready" : "classifying";
}

function codingsBy(
  rows: ReviewRow[],
  matches: (reviewer: string) => boolean,
): Coding[] {
  return rows
    .filter((row) => matches(row.reviewer))
    .map((row) => ({ field: row.field, value: row.value }));
}

export function requiredQuickRef(
  record: AirtableRecord<{ QuickRef?: string }>,
): string {
  const quickRef = record.fields.QuickRef;
  if (quickRef === undefined || quickRef.trim() === "") {
    throw new Error(`Record ${record.id} is missing QuickRef`);
  }
  return quickRef;
}

export function groupRisksByPaper(
  risks: AirtableRecord<RiskFields>[],
): Map<string, AirtableRecord<RiskFields>[]> {
  const result = new Map<string, AirtableRecord<RiskFields>[]>();
  for (const risk of risks) {
    const quickRef = requiredQuickRef(risk);
    const list = result.get(quickRef);
    if (list === undefined) {
      result.set(quickRef, [risk]);
    } else {
      list.push(risk);
    }
  }
  return result;
}
