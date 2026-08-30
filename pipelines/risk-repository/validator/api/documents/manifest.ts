import type { ManifestEntry } from "../../shared/screening.js";
import {
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
} from "../_airtable.js";
import { readAirtableEnv } from "../_env.js";
import { errorResponse, handleError, queryParam } from "../_http.js";
import { type DecisionFields, type DocumentFields, STAGE } from "../_types.js";

export default async function handler(request: Request): Promise<Response> {
  if (request.method !== "GET") {
    return errorResponse(405, "Method not allowed");
  }

  const reviewer = queryParam(new URL(request.url).searchParams, "reviewer");
  if (reviewer === null) {
    return errorResponse(400, "reviewer query parameter is required");
  }

  try {
    const airtable = readAirtableEnv(process.env);
    const [documents, decisions] = await Promise.all([
      listAllRecords<DocumentFields>(
        airtable.pat,
        airtable.baseId,
        airtable.documentsTable,
        {
          view: airtable.documentsView,
          fields: ["QuickRef", "DocTitle", "Abstract"],
        },
      ),
      listAllRecords<DecisionFields>(
        airtable.pat,
        airtable.baseId,
        airtable.decisionsTable,
        {
          filterByFormula: `AND({Reviewer}="${escapeFormulaString(reviewer)}", {Stage}="${STAGE}")`,
          fields: ["Document", "Decision", "Comments"],
        },
      ),
    ]);

    const byDocId = indexDecisionsByDocument(decisions);

    const entries: ManifestEntry[] = documents.map((doc) => {
      const readableId = doc.fields.QuickRef;
      if (readableId === undefined) {
        throw new Error(`Document ${doc.id} is missing QuickRef`);
      }
      const decision = byDocId.get(doc.id);
      return {
        id: doc.id,
        readableId,
        title: doc.fields.DocTitle ?? null,
        abstract: doc.fields.Abstract ?? null,
        decision: decision?.fields.Decision ?? null,
        comments: decision?.fields.Comments ?? null,
        decisionId: decision?.id ?? null,
      };
    });

    return Response.json({ documents: entries });
  } catch (error) {
    return handleError(error);
  }
}

function indexDecisionsByDocument(
  decisions: AirtableRecord<DecisionFields>[],
): Map<string, AirtableRecord<DecisionFields>> {
  const result = new Map<string, AirtableRecord<DecisionFields>>();
  for (const dec of decisions) {
    const docs = dec.fields.Document;
    if (docs === undefined) {
      continue;
    }
    for (const docId of docs) {
      result.set(docId, dec);
    }
  }
  return result;
}
