import { describe, expect, it } from "vitest";
import {
  cellKey,
  cellQuotes,
  mitigationsByCell,
  quotesByMitigation,
} from "@/lib/cells";
import type { Mitigation, Quote } from "@/lib/types";

function mitigation(
  recordId: string,
  companyId: string,
  practiceRecordIds: string[],
): Mitigation {
  return {
    record_id: recordId,
    mitigation_id: `${companyId}__2.2__1`,
    company_id: companyId,
    domain_record_id: "recDomain22",
    instrument_record_id: "recInstrument23",
    practice_record_ids: practiceRecordIds,
    name: "Board oversight of AI",
    search_reasoning: "The board oversees AI.",
    instrument_reasoning: "An internal policy.",
    practice_tags: null,
    pipeline_run: "2026-11-15T22-05-15+0000",
  };
}

function quote(evidenceId: string, mitigationRecordId: string): Quote {
  return {
    evidence_id: evidenceId,
    mitigation_record_id: mitigationRecordId,
    document_id: "Bank_001",
    excerpt_id: "Bank_001_excerpt1",
    quote: "Our board oversees AI.",
    strength: "stated",
    location: null,
  };
}

const BANK_FIRST = mitigation("recBank1", "recBank", ["recModelCards"]);
const BANK_SECOND = mitigation("recBank2", "recBank", []);
const RETAIL = mitigation("recRetail1", "recRetail", [
  "recModelCards",
  "recRedTeaming",
]);

describe("mitigationsByCell", () => {
  it("groups mitigations by company and domain", () => {
    expect(
      mitigationsByCell([BANK_FIRST, BANK_SECOND, RETAIL], "Domain"),
    ).toEqual(
      new Map([
        [cellKey("recBank", "recDomain22"), [BANK_FIRST, BANK_SECOND]],
        [cellKey("recRetail", "recDomain22"), [RETAIL]],
      ]),
    );
  });

  it("puts a mitigation in the cell of each of its practices", () => {
    expect(
      mitigationsByCell([BANK_FIRST, BANK_SECOND, RETAIL], "Practice"),
    ).toEqual(
      new Map([
        [cellKey("recBank", "recModelCards"), [BANK_FIRST]],
        [cellKey("recRetail", "recModelCards"), [RETAIL]],
        [cellKey("recRetail", "recRedTeaming"), [RETAIL]],
      ]),
    );
  });
});

describe("cellQuotes", () => {
  it("lists the quotes of each mitigation in turn", () => {
    const first = quote("Bank__2.2__1.1", "recBank1");
    const second = quote("Bank__2.2__2.1", "recBank2");
    const third = quote("Bank__2.2__1.2", "recBank1");
    const quotes = quotesByMitigation([first, second, third]);

    expect(cellQuotes([BANK_FIRST, BANK_SECOND], quotes)).toEqual([
      first,
      third,
      second,
    ]);
  });

  it("rejects a mitigation without quotes", () => {
    expect(() => cellQuotes([BANK_FIRST], new Map())).toThrow(
      "Mitigation recBank__2.2__1 has no quotes",
    );
  });
});
