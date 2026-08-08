import type { VercelRequest, VercelResponse } from "@vercel/node";
import {
  DECISIONS,
  type Decision,
  type DecisionRequest,
} from "../shared/screening.js";
import {
  AirtableError,
  type AirtableRecord,
  createRecord,
  updateRecord,
} from "./_airtable.js";
import { readAirtableEnv } from "./_env.js";
import { type DecisionFields, STAGE } from "./_types.js";

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

  try {
    const env = readAirtableEnv();
    const fields: DecisionFields = {
      Document: [parsed.documentId],
      Reviewer: parsed.reviewer,
      Stage: STAGE,
      Decision: parsed.decision,
      Comments: parsed.comments ?? "",
    };
    let record: AirtableRecord<DecisionFields>;
    if (parsed.decisionId === null) {
      record = await createRecord(
        env.pat,
        env.baseId,
        env.decisionsTable,
        fields,
      );
    } else {
      record = await updateRecord(
        env.pat,
        env.baseId,
        env.decisionsTable,
        parsed.decisionId,
        fields,
      );
    }
    res.status(200).json({
      documentId: parsed.documentId,
      decisionId: record.id,
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
  const decisionId = b.decisionId;
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
    decisionId !== null &&
    decisionId !== undefined &&
    typeof decisionId !== "string"
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
    decisionId:
      typeof decisionId === "string" && decisionId !== "" ? decisionId : null,
    decision,
    comments: typeof comments === "string" ? comments : null,
  };
}

function isDecision(value: string): value is Decision {
  return (DECISIONS as readonly string[]).includes(value);
}
