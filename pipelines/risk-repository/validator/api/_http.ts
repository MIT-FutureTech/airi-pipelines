import type { VercelRequest } from "@vercel/node";
import { AirtableError } from "./_airtable.js";

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
  return Response.json({ error: message }, { status: 500 });
}

export function searchParams(req: VercelRequest): URLSearchParams {
  return new URLSearchParams(req.url?.split("?")[1] ?? "");
}

export function queryParam(
  params: URLSearchParams,
  name: string,
): string | null {
  const values = params.getAll(name);
  if (values.length !== 1) {
    return null;
  }
  const trimmed = values[0].trim();
  return trimmed === "" ? null : trimmed;
}
