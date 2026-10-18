// biome-ignore-all lint/style/useNamingConvention: these fixtures mirror what Python outputs
import { describe, expect, it } from "vitest";
import { cellKey, evidenceByCell } from "@/lib/cells";
import type { CompanyDocument, LocatedEvidence } from "@/lib/types";

function companyDocument(
  documentId: string,
  companyId: string,
): CompanyDocument {
  return {
    document_id: documentId,
    company_id: companyId,
    title: `${documentId} title`,
    doc_type: "Annual report",
    date: null,
    date_precision: null,
    link: `https://example.com/${documentId}.pdf`,
  };
}

function evidence(documentId: string, code: string): LocatedEvidence {
  return {
    document_id: documentId,
    code,
    mitigation: "Board oversight of AI",
    quote: "Our board oversees AI.",
    strength: "stated",
    excerpt_id: `${documentId}_excerpt1`,
    location: null,
  };
}

const DOCUMENTS = [
  companyDocument("Bank_001", "recBank"),
  companyDocument("Bank_002", "recBank"),
  companyDocument("Retail_001", "recRetail"),
];

describe("evidenceByCell", () => {
  it("groups evidence by company and code", () => {
    const first = evidence("Bank_001", "2.2");
    const second = evidence("Bank_002", "2.2");
    const third = evidence("Bank_001", "1.7");
    const fourth = evidence("Retail_001", "2.2");

    const cells = evidenceByCell([first, second, third, fourth], DOCUMENTS);

    expect(cells).toEqual(
      new Map([
        [cellKey("recBank", "2.2"), [first, second]],
        [cellKey("recBank", "1.7"), [third]],
        [cellKey("recRetail", "2.2"), [fourth]],
      ]),
    );
  });

  it("rejects evidence from an unknown document", () => {
    expect(() =>
      evidenceByCell([evidence("Insurer_001", "2.2")], DOCUMENTS),
    ).toThrow("unknown document Insurer_001");
  });
});
