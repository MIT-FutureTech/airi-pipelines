import type { EvidenceField, EvidenceItem } from "@shared/classification";

// Supported shapes:
//   - JSON string containing an array of objects
//   - Plain string
export function parseEvidence(raw: string | undefined): EvidenceItem[] {
  if (raw === undefined || raw.trim() === "") {
    return [];
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [asItem(raw, 0)];
  }
  const units = Array.isArray(parsed) ? parsed : [parsed];
  return units.map(asItem).filter((item) => item.fields.length > 0);
}

function asItem(unit: unknown, index: number): EvidenceItem {
  if (typeof unit !== "object" || unit === null || Array.isArray(unit)) {
    return { index, fields: namedFields("text", unit) };
  }
  const fields: EvidenceField[] = [];
  for (const [key, value] of Object.entries(unit)) {
    fields.push(...namedFields(key, value));
  }
  return { index, fields };
}

function namedFields(key: string, value: unknown): EvidenceField[] {
  const rendered = renderValue(value);
  return rendered === "" ? [] : [{ key, value: rendered }];
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value.trim();
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value
      .map(renderValue)
      .filter((entry) => entry !== "")
      .join("; ");
  }
  return JSON.stringify(value);
}
