// biome-ignore-all lint/style/useNamingConvention: these fixtures mirror what Python outputs
import { describe, expect, it } from "vitest";
import { strongest } from "@/lib/strength";
import type { LocatedEvidence, Strength } from "@/lib/types";

function evidence(strength: Strength): LocatedEvidence {
  return {
    document_id: "Bank_001",
    code: "2.2",
    mitigation: "Board oversight of AI",
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
