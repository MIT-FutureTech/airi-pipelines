import {
  AirtableError,
  type AirtableRecord,
  escapeFormulaString,
  listAllRecords,
} from "@api/_airtable";
import { readAirtableEnv } from "@api/_env";
import type { ManifestEntry } from "@api/_shared";
import { type DocumentFields, STAGE, type ValidationFields } from "@api/_types";
import type { VercelRequest, VercelResponse } from "@vercel/node";

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

  const env = readAirtableEnv();

  try {
    const [documents, validations] = await Promise.all([
      listAllRecords<DocumentFields>(env.pat, env.baseId, env.documentsTable, {
        view: env.documentsView,
        fields: ["QuickRef", "DocTitle"],
      }),
      listAllRecords<ValidationFields>(
        env.pat,
        env.baseId,
        env.validationsTable,
        {
          filterByFormula: `AND({Reviewer}="${escapeFormulaString(reviewer)}", {Stage}="${STAGE}")`,
          fields: ["Document", "Decision", "Comments"],
        },
      ),
    ]);

    const byDocId = indexValidationsByDocument(validations);

    const entries: ManifestEntry[] = documents.map((doc) => {
      const readableId = doc.fields.QuickRef;
      if (readableId === undefined) {
        throw new Error(`Document ${doc.id} is missing QuickRef`);
      }
      const validation = byDocId.get(doc.id);
      return {
        id: doc.id,
        readableId,
        title: doc.fields.DocTitle ?? null,
        decision: validation?.fields.Decision ?? null,
        comments: validation?.fields.Comments ?? null,
        validationId: validation?.id ?? null,
      };
    });

    res.status(200).json({ documents: entries });
  } catch (error) {
    handleError(res, error);
  }
}

function indexValidationsByDocument(
  validations: AirtableRecord<ValidationFields>[],
): Map<string, AirtableRecord<ValidationFields>> {
  const result = new Map<string, AirtableRecord<ValidationFields>>();
  for (const v of validations) {
    const docs = v.fields.Document;
    if (docs === undefined) {
      continue;
    }
    for (const docId of docs) {
      result.set(docId, v);
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
