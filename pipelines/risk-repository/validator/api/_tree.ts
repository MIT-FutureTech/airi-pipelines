import { REJECTED_ORIGIN, type RiskFields } from "../shared/classification.js";
import type { AirtableRecord } from "./_airtable.js";

export function isRejected(risk: AirtableRecord<RiskFields>): boolean {
  return risk.fields.Origin === REJECTED_ORIGIN;
}

export function parentId(risk: AirtableRecord<RiskFields>): string | null {
  return risk.fields.Parent?.[0] ?? null;
}

// A risk is codable when it survived extraction review and has no surviving
// children. Leaf-ness has to be computed after dropping rejected rows: a node
// whose every child was rejected becomes a leaf and must then be classifiable.
export function codableIds(risks: AirtableRecord<RiskFields>[]): Set<string> {
  const surviving = risks.filter((risk) => !isRejected(risk));
  const parents = new Set<string>();
  for (const risk of surviving) {
    const parent = parentId(risk);
    if (parent !== null) {
      parents.add(parent);
    }
  }
  const codable = new Set<string>();
  for (const risk of surviving) {
    if (!parents.has(risk.id)) {
      codable.add(risk.id);
    }
  }
  return codable;
}
