// biome-ignore-all lint/style/useNamingConvention: these fixtures mirror what Python outputs
import { describe, expect, it } from "vitest";
import { sortByStrength, strongest } from "@/lib/strength";
import type { Quote, Strength } from "@/lib/types";

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
