// biome-ignore-all lint/style/useNamingConvention: these fixtures mirror what Python outputs
import { describe, expect, it } from "vitest";
import {
  sortByStrength,
  sortByStrongestQuote,
  strongest,
} from "@/lib/strength";
import type { Mitigation, Quote, Strength } from "@/lib/types";

function evidence(strength: Strength): Quote {
  return {
    evidence_id: "Bank__2.2__1.1",
    mitigation_record_id: "recMitigation",
    document_id: "Bank_001",
    quote: "Our board oversees AI.",
    strength,
    excerpt_id: "Bank_001_excerpt1",
    location: null,
  };
}

describe("strongest", () => {
  it("picks described over stated and reference", () => {
    const items = [
      evidence("reference"),
      evidence("described"),
      evidence("stated"),
    ];

    expect(strongest(items)).toBe("described");
  });

  it("picks stated over reference", () => {
    expect(strongest([evidence("reference"), evidence("stated")])).toBe(
      "stated",
    );
  });

  it("rejects an empty list", () => {
    expect(() => strongest([])).toThrow("No evidence to rate");
  });
});

describe("sortByStrength", () => {
  it("puts stronger quotes first and keeps the order within a rating", () => {
    const firstReference = { ...evidence("reference"), quote: "First" };
    const stated = evidence("stated");
    const secondReference = { ...evidence("reference"), quote: "Second" };
    const described = evidence("described");

    const sorted = sortByStrength([
      firstReference,
      stated,
      secondReference,
      described,
    ]);

    expect(sorted).toEqual([
      described,
      stated,
      firstReference,
      secondReference,
    ]);
  });
});

describe("sortByStrongestQuote", () => {
  function mitigation(recordId: string): Mitigation {
    return {
      record_id: recordId,
      mitigation_id: `Bank__2.2__${recordId}`,
      company_id: "recBank",
      domain_record_id: "recDomain22",
      instrument_record_id: "recInstrument23",
      practice_record_ids: [],
      name: "Board oversight of AI",
      search_reasoning: "The board oversees AI.",
      instrument_reasoning: "An internal policy.",
      practice_tags: null,
      pipeline_run: "2026-11-15T22-05-15+0000",
    };
  }

  it("puts mitigations with stronger quotes first", () => {
    const onlyReferenced = mitigation("recReferenced");
    const described = mitigation("recDescribed");
    const stated = mitigation("recStated");
    const quotes = new Map([
      ["recReferenced", [evidence("reference")]],
      ["recDescribed", [evidence("reference"), evidence("described")]],
      ["recStated", [evidence("stated")]],
    ]);

    expect(
      sortByStrongestQuote([onlyReferenced, described, stated], quotes),
    ).toEqual([described, stated, onlyReferenced]);
  });
});
