import type { VercelRequest, VercelResponse } from "@vercel/node";
import {
  type CodingWrite,
  REVIEW_FIELD_VALUES,
  REVIEW_FIELDS,
  REVIEW_MODES,
  type ReviewField,
  type ReviewFields,
  type ReviewMode,
  type SaveCodingsRequest,
  type SaveCodingsResponse,
} from "../shared/classification.js";
import { conflictsWithNotARisk } from "../shared/coding.js";
import {
  createRecords,
  deleteRecords,
  type RecordUpdate,
  updateRecords,
} from "./_airtable.js";
import { readAirtableEnv } from "./_env.js";
import { handleError } from "./_http.js";
import {
  isPipelineReviewer,
  toReviewResponse,
  toReviewRow,
} from "./_reviews.js";

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
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
    const env = readAirtableEnv(process.env);
    const creates: ReviewFields[] = [];
    const updates: RecordUpdate<ReviewFields>[] = [];
    for (const coding of parsed.codings) {
      const fields: ReviewFields = {
        Risk: [parsed.riskId],
        Reviewer: parsed.reviewer,
        Field: coding.field,
        Value: coding.value,
        Mode: parsed.mode,
        Comment: coding.comment ?? "",
      };
      if (coding.reviewId === null) {
        creates.push(fields);
      } else {
        updates.push({ id: coding.reviewId, fields });
      }
    }

    await deleteRecords(
      env.pat,
      env.baseId,
      env.reviewsTable,
      parsed.staleReviewIds,
    );
    const [created, updated] = await Promise.all([
      createRecords(env.pat, env.baseId, env.reviewsTable, creates),
      updateRecords(env.pat, env.baseId, env.reviewsTable, updates),
    ]);

    const responses = [...created, ...updated]
      .map(toReviewRow)
      .map(toReviewResponse);
    responses.sort(
      (a, b) => REVIEW_FIELDS.indexOf(a.field) - REVIEW_FIELDS.indexOf(b.field),
    );
    const body: SaveCodingsResponse = { riskId: parsed.riskId, responses };
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
  }
}

export function parseBody(body: unknown): SaveCodingsRequest | null {
  if (typeof body !== "object" || body === null) {
    return null;
  }
  const b = body as Record<string, unknown>;
  const { reviewer, riskId, mode } = b;
  if (
    typeof reviewer !== "string" ||
    reviewer.trim() === "" ||
    typeof riskId !== "string" ||
    riskId === "" ||
    typeof mode !== "string" ||
    !isMode(mode)
  ) {
    return null;
  }
  const codings = parseCodings(b.codings);
  const staleReviewIds = parseIds(b.staleReviewIds);
  if (codings === null || staleReviewIds === null) {
    return null;
  }
  const kept = new Set(codings.map((coding) => coding.reviewId));
  if (staleReviewIds.some((id) => kept.has(id))) {
    return null;
  }
  return { reviewer: reviewer.trim(), riskId, mode, codings, staleReviewIds };
}

function parseCodings(value: unknown): CodingWrite[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  const codings: CodingWrite[] = [];
  const fields = new Set<ReviewField>();
  for (const item of value) {
    const coding = parseCoding(item);
    if (coding === null || fields.has(coding.field)) {
      return null;
    }
    fields.add(coding.field);
    codings.push(coding);
  }
  if (conflictsWithNotARisk(codings)) {
    return null;
  }
  return codings;
}

function parseCoding(item: unknown): CodingWrite | null {
  if (typeof item !== "object" || item === null) {
    return null;
  }
  const coding = item as Record<string, unknown>;
  const { reviewId, field, value, comment } = coding;
  if (typeof field !== "string" || !isField(field)) {
    return null;
  }
  if (typeof value !== "string" || !isValidValue(field, value)) {
    return null;
  }
  if (reviewId !== null && (typeof reviewId !== "string" || reviewId === "")) {
    return null;
  }
  if (comment !== null && typeof comment !== "string") {
    return null;
  }
  return { reviewId, field, value, comment };
}

function parseIds(value: unknown): string[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  const ids: string[] = [];
  for (const id of value) {
    if (typeof id !== "string" || id === "") {
      return null;
    }
    ids.push(id);
  }
  return ids;
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
