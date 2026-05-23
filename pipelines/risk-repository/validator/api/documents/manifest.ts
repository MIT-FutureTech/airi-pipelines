import type { VercelRequest, VercelResponse } from "@vercel/node";
import {
  AirtableError,
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
} from "../_airtable.js";
import { readAirtableEnv } from "../_env.js";
import type { ManifestEntry } from "../_shared.js";
import { type DecisionFields, type DocumentFields, STAGE } from "../_types.js";

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const reviewer = req.query.reviewer;
  if (typeof reviewer !== "string" || reviewer.trim() === "") {
    res.status(400).json({ error: "reviewer query parameter is required" });
    return;
  }

  try {
    const env = readAirtableEnv();
    const [documents, decisions] = await Promise.all([
      listAllRecords<DocumentFields>(env.pat, env.baseId, env.documentsTable, {
        view: env.documentsView,
        fields: ["QuickRef", "DocTitle", "Abstract"],
      }),
      listAllRecords<DecisionFields>(env.pat, env.baseId, env.decisionsTable, {
        filterByFormula: `AND({Reviewer}="${escapeFormulaString(reviewer)}", {Stage}="${STAGE}")`,
        fields: ["Document", "Decision", "Comments"],
      }),
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

    res.status(200).json({ documents: entries });
  } catch (error) {
    handleError(res, error);
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
