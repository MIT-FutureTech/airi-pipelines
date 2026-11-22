import { AirtableError } from "@api/_airtable";

export function errorResponse(status: number, message: string): Response {
  return Response.json({ error: message }, { status });
}

export function handleError(error: unknown): Response {
  if (error instanceof AirtableError) {
    return Response.json(
      { error: "Airtable request failed", detail: error.body },
      { status: 502 },
    );
  }
  const message = error instanceof Error ? error.message : String(error);
  return errorResponse(500, message);
}
