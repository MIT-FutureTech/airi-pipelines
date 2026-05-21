import { AirtableError, getRecord } from "@api/_airtable";
import { readAirtableEnv } from "@api/_env";
import type { DocumentFields } from "@api/_types";
import type { VercelRequest, VercelResponse } from "@vercel/node";

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const id = req.query.id;
  if (typeof id !== "string" || id === "") {
    res.status(400).json({ error: "id is required" });
    return;
  }

  const env = readAirtableEnv();

  try {
    const record = await getRecord<DocumentFields>(
      env.pat,
      env.baseId,
      env.documentsTable,
      id,
    );
    const readableId = record.fields.QuickRef;
    if (readableId === undefined) {
      throw new Error(`Document ${record.id} is missing QuickRef`);
    }
    res.status(200).json({
      id: record.id,
      readableId,
      title: record.fields.DocTitle ?? null,
      abstract: record.fields.Abstract ?? null,
    });
  } catch (error) {
    if (error instanceof AirtableError) {
      const status = error.status === 404 ? 404 : 502;
      res
        .status(status)
        .json({ error: "Airtable request failed", detail: error.body });
      return;
    }
    const message = error instanceof Error ? error.message : String(error);
    res.status(500).json({ error: message });
  }
}
