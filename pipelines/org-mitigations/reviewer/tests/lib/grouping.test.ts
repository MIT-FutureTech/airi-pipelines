// biome-ignore-all lint/style/useNamingConvention: these fixtures mirror what Python outputs
import { describe, expect, it } from "vitest";
import { groupByDocument } from "@/lib/grouping";
import type { LocatedEvidence, Strength } from "@/lib/types";

function evidence(
  documentId: string,
  strength: Strength,
  quote: string,
): LocatedEvidence {
  return {
    document_id: documentId,
    code: "2.2",
    mitigation: "Board oversight of AI",
    quote,
    strength,
    excerpt_id: `${documentId}_excerpt1`,
    location: null,
  };
}

describe("groupByDocument", () => {
  it("orders documents by their strongest quotes", () => {
    const a1 = evidence("A", "stated", "A1");
    const a2 = evidence("A", "reference", "A2");
    const b1 = evidence("B", "reference", "B1");
    const b2 = evidence("B", "described", "B2");
    const c1 = evidence("C", "stated", "C1");
    const c2 = evidence("C", "stated", "C2");

    const groups = groupByDocument([a1, a2, b1, b2, c1, c2]);

    expect(groups).toEqual([
      { documentId: "B", evidence: [b2, b1] },
      { documentId: "C", evidence: [c1, c2] },
      { documentId: "A", evidence: [a1, a2] },
    ]);
  });

  it("keeps the original order of equally strong documents", () => {
    const a = evidence("A", "stated", "A1");
    const b = evidence("B", "stated", "B1");

    const groups = groupByDocument([a, b]);

    expect(groups.map((group) => group.documentId)).toEqual(["A", "B"]);
  });
});
