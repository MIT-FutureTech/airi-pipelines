import type { AirtableRecord } from "@api/_airtable";
import type { AirtableEnv } from "@api/_env";
import {
  fetchVisibleReviews,
  fetchVisibleReviewsForPaper,
  indexReviewsByRisk,
  isPipelineReviewer,
  paperScopeFormula,
  requiredRiskId,
  reviewerScopeFormula,
  toReviewResponse,
} from "@api/_reviews";
import type { ReviewFields } from "@shared/classification";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const LOOKUP = "ReadableId (from Risk)";

const ENV: AirtableEnv = {
  pat: "pat-test",
  baseId: "appTest",
  documentsTable: "Documents",
  documentsView: "Grid",
  decisionsTable: "Decisions",
  risksTable: "Risks",
  reviewsTable: "Reviews",
  proposedExtractionsTable: "Proposed Extractions",
  fullTextTable: "Full-Text Screening",
};

function review(
  id: string,
  fields: ReviewFields,
): AirtableRecord<ReviewFields> {
  return { id, createdTime: "2026-01-01T00:00:00.000Z", fields };
}

let requested: URL[];

beforeEach(() => {
  requested = [];
  vi.stubGlobal("fetch", (input: string) => {
    requested.push(new URL(input));
    return Promise.resolve(
      new Response(JSON.stringify({ records: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function formulas(): string[] {
  return requested.map((url) => url.searchParams.get("filterByFormula") ?? "");
}

describe("paperScopeFormula", () => {
  it("compares the quick ref together with its trailing dot", () => {
    expect(paperScopeFormula("Lee2025")).toBe(
      `LEFT(ARRAYJOIN({${LOOKUP}}), 8)="Lee2025."`,
    );
  });

  it("lengthens the comparison for a quick ref that extends another", () => {
    expect(paperScopeFormula("Lee2025a")).toBe(
      `LEFT(ARRAYJOIN({${LOOKUP}}), 9)="Lee2025a."`,
    );
  });

  it("escapes a quoted quick ref but counts its unescaped length", () => {
    expect(paperScopeFormula('Lee"2025')).toBe(
      `LEFT(ARRAYJOIN({${LOOKUP}}), 9)="Lee\\"2025."`,
    );
  });

  it("escapes a backslash the same way", () => {
    expect(paperScopeFormula("Lee\\2025")).toBe(
      `LEFT(ARRAYJOIN({${LOOKUP}}), 9)="Lee\\\\2025."`,
    );
  });
});

describe("reviewerScopeFormula", () => {
  it("asks for nobody but the reviewer in blind mode", () => {
    expect(reviewerScopeFormula("alice", "blind")).toBe('{Reviewer}="alice"');
  });

  it("never mentions the pipeline in blind mode", () => {
    expect(reviewerScopeFormula("alice", "blind")).not.toContain("pipeline:");
  });

  it("adds the pipeline in anchored mode", () => {
    expect(reviewerScopeFormula("alice", "anchored")).toBe(
      'OR({Reviewer}="alice", LEFT({Reviewer}, 9)="pipeline:")',
    );
  });

  it("escapes a quoted reviewer name", () => {
    expect(reviewerScopeFormula('al"ice', "blind")).toBe(
      '{Reviewer}="al\\"ice"',
    );
  });
});

describe("fetchVisibleReviewsForPaper", () => {
  it("asks Airtable for nothing outside the reviewer's own rows in blind mode", async () => {
    await fetchVisibleReviewsForPaper(ENV, "alice", "Lee2025", "blind");
    expect(formulas()).toEqual([
      `AND(${paperScopeFormula("Lee2025")}, ${reviewerScopeFormula("alice", "blind")})`,
    ]);
    expect(formulas()[0]).not.toContain("pipeline:");
  });

  it("asks for the pipeline's rows too in anchored mode", async () => {
    await fetchVisibleReviewsForPaper(ENV, "alice", "Lee2025", "anchored");
    expect(formulas()[0]).toContain("pipeline:");
  });

  it("scopes to the requested paper", async () => {
    await fetchVisibleReviewsForPaper(ENV, "alice", "Lee2025", "blind");
    expect(formulas()[0]).toContain('="Lee2025."');
  });
});

describe("fetchVisibleReviews", () => {
  it("always includes the pipeline, since the paper list reports its progress", async () => {
    await fetchVisibleReviews(ENV, "alice");
    expect(formulas().length).toBeGreaterThan(0);
    for (const formula of formulas()) {
      expect(formula).toContain("pipeline:");
      expect(formula).toContain('{Reviewer}="alice"');
    }
  });
});

describe("isPipelineReviewer", () => {
  it("recognises the pipeline's reviewer names", () => {
    expect(isPipelineReviewer("pipeline:v1")).toBe(true);
    expect(isPipelineReviewer("pipeline:")).toBe(true);
  });

  it("does not claim a human", () => {
    expect(isPipelineReviewer("alice")).toBe(false);
    expect(isPipelineReviewer("")).toBe(false);
    expect(isPipelineReviewer("Pipeline:v1")).toBe(false);
    expect(isPipelineReviewer("my pipeline:v1")).toBe(false);
  });
});

describe("indexReviewsByRisk", () => {
  it("groups rows under the risk they link to", () => {
    const rows = [
      review("a", { Risk: ["risk1"] }),
      review("b", { Risk: ["risk2"] }),
      review("c", { Risk: ["risk1"] }),
    ];
    const index = indexReviewsByRisk(rows);
    expect(index.get("risk1")?.map((row) => row.id)).toEqual(["a", "c"]);
    expect(index.get("risk2")?.map((row) => row.id)).toEqual(["b"]);
  });

  it("refuses a row that links to no risk", () => {
    expect(() => indexReviewsByRisk([review("a", {})])).toThrow("a");
    expect(() => indexReviewsByRisk([review("b", { Risk: [] })])).toThrow("b");
  });

  it("is empty for no rows at all", () => {
    expect(indexReviewsByRisk([]).size).toBe(0);
  });
});

describe("requiredRiskId", () => {
  it("returns the linked risk", () => {
    expect(requiredRiskId(review("a", { Risk: ["risk1"] }))).toBe("risk1");
  });

  it("takes the first of several links", () => {
    expect(requiredRiskId(review("a", { Risk: ["risk1", "risk2"] }))).toBe(
      "risk1",
    );
  });

  it("names the offending row when there is no link", () => {
    expect(() => requiredRiskId(review("recBad", {}))).toThrow("recBad");
    expect(() => requiredRiskId(review("recBad", { Risk: [] }))).toThrow(
      "recBad",
    );
  });
});

describe("toReviewResponse", () => {
  it("carries the coding across", () => {
    const row = review("rec1", {
      Field: "entity",
      Value: "human",
      Mode: "blind",
      Comment: "because",
    });
    expect(toReviewResponse(row)).toEqual({
      id: "rec1",
      field: "entity",
      value: "human",
      mode: "blind",
      comment: "because",
    });
  });

  it("reports a missing comment as null", () => {
    const row = review("rec1", {
      Field: "entity",
      Value: "human",
      Mode: "blind",
    });
    expect(toReviewResponse(row).comment).toBeNull();
  });

  it("refuses a row that is missing part of the coding", () => {
    expect(() =>
      toReviewResponse(review("rec1", { Value: "human", Mode: "blind" })),
    ).toThrow("rec1");
    expect(() =>
      toReviewResponse(review("rec1", { Field: "entity", Mode: "blind" })),
    ).toThrow("rec1");
    expect(() =>
      toReviewResponse(review("rec1", { Field: "entity", Value: "human" })),
    ).toThrow("rec1");
  });
});
