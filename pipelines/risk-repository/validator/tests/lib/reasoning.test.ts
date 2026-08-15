import type { ReviewField, ReviewResponse } from "@shared/classification";
import { describe, expect, it } from "vitest";
import { groupReasoning } from "@/lib/reasoning";

function response(field: ReviewField, comment: string | null): ReviewResponse {
  return {
    id: `rec-${field}`,
    field,
    value: "human",
    mode: "anchored",
    comment,
  };
}

describe("groupReasoning", () => {
  it("returns nothing when there are no responses", () => {
    expect(groupReasoning([])).toEqual([]);
  });

  it("collapses the fields that share one comment", () => {
    expect(
      groupReasoning([
        response("entity", "same reason"),
        response("intent", "same reason"),
      ]),
    ).toEqual([{ fields: ["entity", "intent"], comment: "same reason" }]);
  });

  it("keeps distinct comments apart", () => {
    expect(
      groupReasoning([
        response("entity", "one reason"),
        response("intent", "another reason"),
      ]),
    ).toEqual([
      { fields: ["entity"], comment: "one reason" },
      { fields: ["intent"], comment: "another reason" },
    ]);
  });

  it("orders groups and their fields by the canonical field order", () => {
    const groups = groupReasoning([
      response("subdomain", "shared"),
      response("intent", "solo"),
      response("validity", "shared"),
    ]);
    expect(groups).toEqual([
      { fields: ["validity", "subdomain"], comment: "shared" },
      { fields: ["intent"], comment: "solo" },
    ]);
  });

  it("trims comments before comparing them", () => {
    expect(
      groupReasoning([
        response("entity", "  reason  "),
        response("intent", "reason"),
      ]),
    ).toEqual([{ fields: ["entity", "intent"], comment: "reason" }]);
  });

  it("skips responses with nothing to say", () => {
    expect(
      groupReasoning([
        response("entity", null),
        response("intent", ""),
        response("timing", "   "),
      ]),
    ).toEqual([]);
  });

  it("lets the last response for a field win", () => {
    expect(
      groupReasoning([
        response("entity", "first"),
        response("entity", "second"),
      ]),
    ).toEqual([{ fields: ["entity"], comment: "second" }]);
  });
});
