import { NOT_A_RISK } from "@shared/classification";
import {
  type Coding,
  conflictsWithNotARisk,
  isCoded,
  isNotARisk,
} from "@shared/coding";
import { describe, expect, it } from "vitest";

const ALL_AXES: Coding[] = [
  { field: "entity", value: "human" },
  { field: "intent", value: "intentional" },
  { field: "timing", value: "pre-deployment" },
  { field: "subdomain", value: "1.1" },
];

const NOT_A_RISK_CODING: Coding = { field: "validity", value: NOT_A_RISK };

describe("isNotARisk", () => {
  it("is true when the not-a-risk verdict is present", () => {
    expect(isNotARisk([NOT_A_RISK_CODING])).toBe(true);
  });

  it("is false for no codings at all", () => {
    expect(isNotARisk([])).toBe(false);
  });

  it("is false when only the causal axes are set", () => {
    expect(isNotARisk(ALL_AXES)).toBe(false);
  });

  it("is false for a validity coding carrying some other value", () => {
    expect(isNotARisk([{ field: "validity", value: "something-else" }])).toBe(
      false,
    );
  });
});

describe("conflictsWithNotARisk", () => {
  it("is false for the not-a-risk verdict on its own", () => {
    expect(conflictsWithNotARisk([NOT_A_RISK_CODING])).toBe(false);
  });

  it("is false for the causal axes on their own", () => {
    expect(conflictsWithNotARisk(ALL_AXES)).toBe(false);
  });

  it("is false for no codings at all", () => {
    expect(conflictsWithNotARisk([])).toBe(false);
  });

  it("is true when not-a-risk is paired with any single axis", () => {
    for (const axis of ALL_AXES) {
      expect(conflictsWithNotARisk([NOT_A_RISK_CODING, axis])).toBe(true);
    }
  });

  it("is true regardless of which side comes first", () => {
    expect(conflictsWithNotARisk([ALL_AXES[0], NOT_A_RISK_CODING])).toBe(true);
  });
});

describe("isCoded", () => {
  it("is false for no codings at all", () => {
    expect(isCoded([])).toBe(false);
  });

  it("is true once all four causal axes are set", () => {
    expect(isCoded(ALL_AXES)).toBe(true);
  });

  it("is false while any single axis is missing", () => {
    for (const missing of ALL_AXES) {
      const partial = ALL_AXES.filter((coding) => coding !== missing);
      expect(isCoded(partial)).toBe(false);
    }
  });

  it("is true for the not-a-risk verdict on its own", () => {
    expect(isCoded([NOT_A_RISK_CODING])).toBe(true);
  });

  it("is true for not-a-risk even alongside a partial set of axes", () => {
    expect(isCoded([NOT_A_RISK_CODING, ALL_AXES[0]])).toBe(true);
  });

  it("is false for a validity coding carrying some other value", () => {
    expect(isCoded([{ field: "validity", value: "something-else" }])).toBe(
      false,
    );
  });

  it("counts distinct fields, not codings", () => {
    const duplicated: Coding[] = [
      { field: "entity", value: "human" },
      { field: "entity", value: "ai" },
      { field: "intent", value: "intentional" },
      { field: "subdomain", value: "1.1" },
    ];
    expect(isCoded(duplicated)).toBe(false);
  });
});
