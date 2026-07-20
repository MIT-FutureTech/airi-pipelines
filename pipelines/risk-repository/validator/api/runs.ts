import type { VercelRequest, VercelResponse } from "@vercel/node";
import { AirtableError, listAllRecords } from "./_airtable.js";
import {
  type ExtractionRunInfo,
  PIPELINE_REVIEWER_PREFIX,
  type ReviewFields,
  type RiskFields,
  type RunsResponse,
} from "./_classification.js";
import { readAirtableEnv } from "./_env.js";

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const env = readAirtableEnv();
    const [risks, pipelineReviews] = await Promise.all([
      listAllRecords<RiskFields>(env.pat, env.baseId, env.risksTable, {
        fields: ["ExtractionRun"],
      }),
      listAllRecords<ReviewFields>(env.pat, env.baseId, env.reviewsTable, {
        filterByFormula: `LEFT({Reviewer}, ${PIPELINE_REVIEWER_PREFIX.length}) = "${PIPELINE_REVIEWER_PREFIX}"`,
        fields: ["Risk", "Reviewer"],
      }),
    ]);

    const riskCounts = new Map<string, number>();
    const riskToRun = new Map<string, string>();
    for (const risk of risks) {
      const run = risk.fields.ExtractionRun;
      if (run === undefined || run === "") {
        continue;
      }
      riskToRun.set(risk.id, run);
      riskCounts.set(run, (riskCounts.get(run) ?? 0) + 1);
    }

    const runPipelineReviewers = new Map<string, Set<string>>();
    for (const review of pipelineReviews) {
      const riskId = review.fields.Risk?.[0];
      const reviewer = review.fields.Reviewer;
      if (riskId === undefined || reviewer === undefined) {
        continue;
      }
      const run = riskToRun.get(riskId);
      if (run === undefined) {
        continue;
      }
      const reviewers = runPipelineReviewers.get(run) ?? new Set<string>();
      reviewers.add(reviewer);
      runPipelineReviewers.set(run, reviewers);
    }

    const runs: ExtractionRunInfo[] = [...riskCounts.entries()]
      .map(([extractionRun, riskCount]) => ({
        extractionRun,
        riskCount,
        pipelineReviewers: [
          ...(runPipelineReviewers.get(extractionRun) ?? []),
        ].sort(),
      }))
      .sort((a, b) => a.extractionRun.localeCompare(b.extractionRun));

    const body: RunsResponse = { runs };
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
  }
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
