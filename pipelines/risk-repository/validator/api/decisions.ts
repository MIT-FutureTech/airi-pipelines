import {
  DECISIONS,
  type Decision,
  type DecisionRequest,
} from "../shared/screening.js";
import {
  type AirtableRecord,
  createRecord,
  updateRecord,
} from "./_airtable.js";
import { readAirtableEnv } from "./_env.js";
import { errorResponse, handleError } from "./_http.js";
import { type DecisionFields, STAGE } from "./_types.js";

export default async function handler(request: Request): Promise<Response> {
  if (request.method !== "POST") {
    return errorResponse(405, "Method not allowed");
  }

  const parsed = parseBody(await request.json().catch(() => null));
  if (parsed === null) {
    return errorResponse(400, "Invalid request body");
  }

  try {
    const airtable = readAirtableEnv(process.env);
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
        airtable.pat,
        airtable.baseId,
        airtable.decisionsTable,
        fields,
      );
    } else {
      record = await updateRecord(
        airtable.pat,
        airtable.baseId,
        airtable.decisionsTable,
        parsed.decisionId,
        fields,
      );
    }
    return Response.json({
      documentId: parsed.documentId,
      decisionId: record.id,
      decision: parsed.decision,
      comments: parsed.comments,
    });
  } catch (error) {
    return handleError(error);
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
