import type { VercelResponse } from "@vercel/node";
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

export function queryString(
  value: string | string[] | undefined,
): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}
