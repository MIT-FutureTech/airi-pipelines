import type { VercelRequest, VercelResponse } from "@vercel/node";
import {
  createRecord,
  deleteRecords,
  escapeFormulaString,
  listAllRecords,
  updateRecord,
} from "./_airtable.js";
import {
  AXIS_FIELDS,
  NOT_A_RISK,
  REVIEW_FIELD_VALUES,
  REVIEW_FIELDS,
  REVIEW_MODES,
  type ReviewField,
  type ReviewFields,
  type ReviewMode,
  type ReviewUpsertRequest,
  type ReviewUpsertResponse,
} from "./_classification.js";
import { readAirtableEnv } from "./_env.js";
import { handleError, queryString } from "./_http.js";
import { isPipelineReviewer } from "./_reviews.js";

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method === "DELETE") {
    await handleDelete(req, res);
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const parsed = parseBody(req.body);
  if (parsed === null) {
    res.status(400).json({ error: "Invalid request body" });
    return;
  }
  if (isPipelineReviewer(parsed.reviewer)) {
    res
      .status(400)
      .json({ error: "Reviewer name is reserved for the pipeline" });
    return;
  }

  try {
    const env = readAirtableEnv();
    const fields: ReviewFields = {
      Risk: [parsed.riskId],
      Reviewer: parsed.reviewer,
      Field: parsed.field,
      Value: parsed.value,
      Mode: parsed.mode,
      Comment: parsed.comment ?? "",
    };
    const record =
      parsed.reviewId === null
        ? await createRecord<ReviewFields>(
            env.pat,
            env.baseId,
            env.reviewsTable,
            fields,
          )
        : await updateRecord<ReviewFields>(
            env.pat,
            env.baseId,
            env.reviewsTable,
            parsed.reviewId,
            fields,
          );

    if (parsed.field === "validity" && parsed.value === NOT_A_RISK) {
      await clearAxisRows(env, parsed.reviewer, parsed.riskId);
    }

    const body: ReviewUpsertResponse = {
      riskId: parsed.riskId,
      reviewId: record.id,
      field: parsed.field,
      value: parsed.value,
    };
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
  }
}

async function handleDelete(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  const reviewId = queryString(req.query.reviewId);
  if (reviewId === null) {
    res.status(400).json({ error: "reviewId query parameter is required" });
    return;
  }
  try {
    const env = readAirtableEnv();
    await deleteRecords(env.pat, env.baseId, env.reviewsTable, [reviewId]);
    res.status(200).json({ reviewId });
  } catch (error) {
    handleError(res, error);
  }
}

async function clearAxisRows(
  env: { pat: string; baseId: string; reviewsTable: string },
  reviewer: string,
  riskId: string,
): Promise<void> {
  const rows = await listAllRecords<ReviewFields>(
    env.pat,
    env.baseId,
    env.reviewsTable,
    {
      filterByFormula: `{Reviewer}="${escapeFormulaString(reviewer)}"`,
      fields: ["Risk", "Field"],
    },
  );
  const axisRowIds = rows
    .filter((row) => {
      const field = row.fields.Field;
      return (
        row.fields.Risk?.[0] === riskId &&
        field !== undefined &&
        (AXIS_FIELDS as readonly string[]).includes(field)
      );
    })
    .map((row) => row.id);
  await deleteRecords(env.pat, env.baseId, env.reviewsTable, axisRowIds);
}

function parseBody(body: unknown): ReviewUpsertRequest | null {
  if (typeof body !== "object" || body === null) {
    return null;
  }
  const b = body as Record<string, unknown>;
  const reviewer = b.reviewer;
  const riskId = b.riskId;
  const field = b.field;
  const value = b.value;
  const mode = b.mode;
  const reviewId = b.reviewId;
  const comment = b.comment;
  if (
    typeof reviewer !== "string" ||
    reviewer.trim() === "" ||
    typeof riskId !== "string" ||
    riskId === "" ||
    typeof field !== "string" ||
    !isField(field) ||
    typeof value !== "string" ||
    !isValidValue(field, value) ||
    typeof mode !== "string" ||
    !isMode(mode)
  ) {
    return null;
  }
  if (
    reviewId !== null &&
    reviewId !== undefined &&
    typeof reviewId !== "string"
  ) {
    return null;
  }
  if (
    comment !== null &&
    comment !== undefined &&
    typeof comment !== "string"
  ) {
    return null;
  }
  return {
    reviewer: reviewer.trim(),
    riskId,
    reviewId: typeof reviewId === "string" && reviewId !== "" ? reviewId : null,
    field,
    value,
    mode,
    comment: typeof comment === "string" ? comment : null,
  };
}

function isField(value: string): value is ReviewField {
  return (REVIEW_FIELDS as readonly string[]).includes(value);
}

function isValidValue(field: ReviewField, value: string): boolean {
  return REVIEW_FIELD_VALUES[field].includes(value);
}

function isMode(value: string): value is ReviewMode {
  return (REVIEW_MODES as readonly string[]).includes(value);
}
