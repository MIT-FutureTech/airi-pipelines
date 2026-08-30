import type { AirtableRecord } from "@api/_airtable";
import { REJECTED_ORIGIN, type RiskFields } from "@shared/classification";

export function isRejected(risk: AirtableRecord<RiskFields>): boolean {
  return risk.fields.Origin === REJECTED_ORIGIN;
}

export function parentId(risk: AirtableRecord<RiskFields>): string | null {
  return risk.fields.Parent?.[0] ?? null;
}

// A risk is codable when it survived extraction review and is a leaf of the
// surviving tree. Leaf-ness has to be computed after dropping rejected rows: a
// node whose every child was rejected becomes a leaf and must then be
// classifiable, and a rejected node's children rise to its nearest surviving
// ancestor rather than detaching from the tree.
export function codableIds(risks: AirtableRecord<RiskFields>[]): Set<string> {
  const byId = new Map(risks.map((risk) => [risk.id, risk]));
  const surviving = risks.filter((risk) => !isRejected(risk));
  const parents = new Set<string>();
  for (const risk of surviving) {
    const parent = survivingAncestorId(byId, risk);
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

function survivingAncestorId(
  byId: Map<string, AirtableRecord<RiskFields>>,
  risk: AirtableRecord<RiskFields>,
): string | null {
  let id = parentId(risk);
  for (let step = 0; id !== null && step < byId.size; step += 1) {
    const parent = byId.get(id);
    if (parent === undefined) {
      return null;
    }
    if (!isRejected(parent)) {
      return parent.id;
    }
    id = parentId(parent);
  }
  return null;
}
