import { STRENGTHS, sortByStrength, strongest } from "@/lib/strength";
import type { LocatedEvidence, Strength } from "@/lib/types";

export interface DocumentGroup {
  documentId: string;
  evidence: LocatedEvidence[];
}

export function groupByDocument(evidence: LocatedEvidence[]): DocumentGroup[] {
  const groups = [...Map.groupBy(evidence, (item) => item.document_id)].map(
    ([documentId, items]) => ({ documentId, evidence: sortByStrength(items) }),
  );
  return groups.toSorted(strongestGroupFirst);
}

function strongestGroupFirst(a: DocumentGroup, b: DocumentGroup): number {
  const strength = strongest(a.evidence);
  const otherStrength = strongest(b.evidence);
  if (strength !== otherStrength) {
    return STRENGTHS.indexOf(strength) - STRENGTHS.indexOf(otherStrength);
  }
  return countAt(b, strength) - countAt(a, strength);
}

function countAt(group: DocumentGroup, strength: Strength): number {
  return group.evidence.filter((item) => item.strength === strength).length;
}
