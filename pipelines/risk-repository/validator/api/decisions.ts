import {
  AirtableError,
  type AirtableRecord,
  createRecord,
  updateRecord,
} from "@api/_airtable";
import { readAirtableEnv } from "@api/_env";
import { DECISIONS, type Decision, type DecisionRequest } from "@api/_shared";
import { STAGE, type ValidationFields } from "@api/_types";
import type { VercelRequest, VercelResponse } from "@vercel/node";

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

  const env = readAirtableEnv();
  const fields: ValidationFields = {
    Document: [parsed.documentId],
    Reviewer: parsed.reviewer,
    Stage: STAGE,
    Decision: parsed.decision,
    Comments: parsed.comments ?? "",
  };

  try {
    let record: AirtableRecord<ValidationFields>;
    if (parsed.validationId === null) {
      record = await createRecord(
        env.pat,
        env.baseId,
        env.validationsTable,
        fields,
      );
    } else {
      record = await updateRecord(
        env.pat,
        env.baseId,
        env.validationsTable,
        parsed.validationId,
        fields,
      );
    }
    res.status(200).json({
      documentId: parsed.documentId,
      validationId: record.id,
      decision: parsed.decision,
      comments: parsed.comments,
    });
  } catch (error) {
    if (error instanceof AirtableError) {
      res
        .status(502)
        .json({ error: "Airtable request failed", detail: error.body });
      return;
    }
    const message = error instanceof Error ? error.message : String(error);
    res.status(500).json({ error: message });
  }
}

function parseBody(body: unknown): DecisionRequest | null {
  if (typeof body !== "object" || body === null) {
    return null;
  }
  const b = body as Record<string, unknown>;
  const reviewer = b.reviewer;
  const documentId = b.documentId;
  const decision = b.decision;
  const validationId = b.validationId;
  const comments = b.comments;
  if (
    typeof reviewer !== "string" ||
    reviewer.trim() === "" ||
    typeof documentId !== "string" ||
    documentId === "" ||
    typeof decision !== "string" ||
    !isDecision(decision)
  ) {
    return null;
  }
  if (
    validationId !== null &&
    validationId !== undefined &&
    typeof validationId !== "string"
  ) {
    return null;
  }
  if (
    comments !== null &&
    comments !== undefined &&
    typeof comments !== "string"
  ) {
    return null;
  }
  return {
    reviewer: reviewer.trim(),
    documentId,
    validationId:
      typeof validationId === "string" && validationId !== ""
        ? validationId
        : null,
    decision,
    comments: typeof comments === "string" ? comments : null,
  };
}

function isDecision(value: string): value is Decision {
  return (DECISIONS as readonly string[]).includes(value);
}
