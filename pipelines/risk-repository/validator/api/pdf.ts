import type {
  FullTextScreeningFields,
  PdfLinkResponse,
  ProposedExtractionFields,
} from "../shared/classification.js";
import { escapeFormulaString, getRecord, listAllRecords } from "./_airtable.js";
import { readAirtableEnv, type WorkerEnv } from "./_env.js";
import { errorResponse, handleError, queryParam } from "./_http.js";

export default async function handler(
  request: Request,
  env: WorkerEnv,
): Promise<Response> {
  if (request.method !== "GET") {
    return errorResponse(405, "Method not allowed");
  }

  const quickRef = queryParam(new URL(request.url).searchParams, "quickRef");
  if (quickRef === null) {
    return errorResponse(400, "quickRef query parameter is required");
  }

  try {
    const airtable = readAirtableEnv(env);
    const papers = await listAllRecords<ProposedExtractionFields>(
      airtable.pat,
      airtable.baseId,
      airtable.proposedExtractionsTable,
      {
        filterByFormula: `{QuickRef}="${escapeFormulaString(quickRef)}"`,
        fields: ["Full-Text Screening"],
      },
    );
    const screeningId = papers[0]?.fields["Full-Text Screening"]?.[0];
    if (screeningId === undefined) {
      return errorResponse(
        404,
        `No full-text screening record linked to ${quickRef}`,
      );
    }

    const screening = await getRecord<FullTextScreeningFields>(
      airtable.pat,
      airtable.baseId,
      airtable.fullTextTable,
      screeningId,
    );
    const attachment = screening.fields.full_text_pdf?.[0];
    if (attachment === undefined) {
      return errorResponse(404, `No PDF attached to ${quickRef}`);
    }

    const body: PdfLinkResponse = {
      quickRef,
      url: attachment.url,
      filename: `${quickRef}.pdf`,
      size: attachment.size,
    };
    // Airtable signs attachment URLs with an expiry, so this must be resolved
    // afresh on every request rather than served from a cache.
    return Response.json(body, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return handleError(error);
  }
}
