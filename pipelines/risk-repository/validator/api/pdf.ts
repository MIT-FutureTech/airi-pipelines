import type { VercelRequest, VercelResponse } from "@vercel/node";
import type {
  FullTextScreeningFields,
  PdfLinkResponse,
  ProposedExtractionFields,
} from "../shared/classification.js";
import { escapeFormulaString, getRecord, listAllRecords } from "./_airtable.js";
import { readAirtableEnv } from "./_env.js";
import { handleError, queryParam, searchParams } from "./_http.js";

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const quickRef = queryParam(searchParams(req), "quickRef");
  if (quickRef === null) {
    res.status(400).json({ error: "quickRef query parameter is required" });
    return;
  }

  try {
    const env = readAirtableEnv(process.env);
    const papers = await listAllRecords<ProposedExtractionFields>(
      env.pat,
      env.baseId,
      env.proposedExtractionsTable,
      {
        filterByFormula: `{QuickRef}="${escapeFormulaString(quickRef)}"`,
        fields: ["Full-Text Screening"],
      },
    );
    const screeningId = papers[0]?.fields["Full-Text Screening"]?.[0];
    if (screeningId === undefined) {
      res
        .status(404)
        .json({ error: `No full-text screening record linked to ${quickRef}` });
      return;
    }

    const screening = await getRecord<FullTextScreeningFields>(
      env.pat,
      env.baseId,
      env.fullTextTable,
      screeningId,
    );
    const attachment = screening.fields.full_text_pdf?.[0];
    if (attachment === undefined) {
      res.status(404).json({ error: `No PDF attached to ${quickRef}` });
      return;
    }

    const body: PdfLinkResponse = {
      quickRef,
      url: attachment.url,
      filename: `${quickRef}.pdf`,
      size: attachment.size,
    };
    // Airtable signs attachment URLs with an expiry, so this must be resolved
    // afresh on every request rather than served from a cache.
    res.setHeader("Cache-Control", "no-store");
    res.status(200).json(body);
  } catch (error) {
    handleError(res, error);
  }
}
