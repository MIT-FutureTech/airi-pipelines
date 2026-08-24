import type { VercelRequest, VercelResponse } from "@vercel/node";
import { AirtableError } from "./_airtable.js";

export function handleError(res: VercelResponse, error: unknown): void {
  if (error instanceof AirtableError) {
    res
      .status(502)
      .json({ error: "Airtable request failed", detail: error.body });
    return;
  }
  const message = error instanceof Error ? error.message : String(error);
  res.status(500).json({ error: message });
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
