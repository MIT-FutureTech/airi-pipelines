import type { AirtableRecord } from "@api/_airtable";
import {
  buildEntry,
  groupRisksByPaper,
  paperState,
  requiredQuickRef,
} from "@api/papers";
import {
  NOT_A_RISK,
  type ProposedExtractionFields,
  type ReviewField,
  type ReviewFields,
  type RiskFields,
} from "@shared/classification";
import { describe, expect, it } from "vitest";

const QUICK_REF = "Lee2025";

function risk(id: string): AirtableRecord<RiskFields> {
  return {
    id,
    createdTime: "2026-01-01T00:00:00.000Z",
    fields: { QuickRef: QUICK_REF, Origin: "model-added, human-approved" },
  };
}

function review(
  reviewer: string,
  field: ReviewField,
  value: string,
): AirtableRecord<ReviewFields> {
  return {
    id: `${reviewer}-${field}`,
    createdTime: "2026-01-01T00:00:00.000Z",
    fields: {
      Reviewer: reviewer,
      Field: field,
      Value: value,
      Mode: "anchored",
    },
  };
}

function fullCoding(reviewer: string): AirtableRecord<ReviewFields>[] {
  return [
    review(reviewer, "entity", "human"),
    review(reviewer, "intent", "intentional"),
    review(reviewer, "timing", "pre-deployment"),
    review(reviewer, "subdomain", "1.1"),
  ];
}

function entryFor(
  risks: AirtableRecord<RiskFields>[],
  codable: Set<string>,
  reviewsByRisk: Map<string, AirtableRecord<ReviewFields>[]>,
  fields: ProposedExtractionFields = {},
) {
  return buildEntry(QUICK_REF, fields, risks, codable, reviewsByRisk, "alice");
}

describe("paperState", () => {
  it("is awaiting-extraction before any risk exists", () => {
    expect(paperState(0, 0, 0)).toBe("awaiting-extraction");
  });

  it("is classifying while the pipeline has codable risks left", () => {
    expect(paperState(5, 3, 0)).toBe("classifying");
    expect(paperState(5, 3, 2)).toBe("classifying");
  });

  it("is ready once the pipeline has coded every codable risk", () => {
    expect(paperState(5, 3, 3)).toBe("ready");
  });

  it("is ready for a paper whose risks are all non-codable", () => {
    expect(paperState(3, 0, 0)).toBe("ready");
  });
});

describe("buildEntry counts", () => {
  it("counts a codable risk the reviewer has fully coded", () => {
    const entry = entryFor(
      [risk("r1")],
      new Set(["r1"]),
      new Map([["r1", fullCoding("alice")]]),
    );
    expect(entry.reviewerCodedCount).toBe(1);
    expect(entry.codableCount).toBe(1);
  });

  it("does not count a partially coded risk", () => {
    const entry = entryFor(
      [risk("r1")],
      new Set(["r1"]),
      new Map([["r1", [review("alice", "entity", "human")]]]),
    );
    expect(entry.reviewerCodedCount).toBe(0);
  });

  it("counts a not-a-risk verdict as coded", () => {
    const entry = entryFor(
      [risk("r1")],
      new Set(["r1"]),
      new Map([["r1", [review("alice", "validity", NOT_A_RISK)]]]),
    );
    expect(entry.reviewerCodedCount).toBe(1);
  });

  it("ignores risks that are not codable, however well coded", () => {
    const entry = entryFor(
      [risk("r1"), risk("r2")],
      new Set(["r1"]),
      new Map([
        ["r1", fullCoding("alice")],
        ["r2", fullCoding("alice")],
      ]),
    );
    expect(entry.codableCount).toBe(1);
    expect(entry.reviewerCodedCount).toBe(1);
  });

  it("keeps the reviewer's progress apart from the pipeline's", () => {
    const entry = entryFor(
      [risk("r1"), risk("r2")],
      new Set(["r1", "r2"]),
      new Map([
        ["r1", [...fullCoding("alice"), ...fullCoding("pipeline:v1")]],
        ["r2", fullCoding("pipeline:v1")],
      ]),
    );
    expect(entry.reviewerCodedCount).toBe(1);
    expect(entry.pipelineCodedCount).toBe(2);
  });

  it("counts nobody else's codings toward either total", () => {
    const entry = entryFor(
      [risk("r1")],
      new Set(["r1"]),
      new Map([["r1", fullCoding("bob")]]),
    );
    expect(entry.reviewerCodedCount).toBe(0);
    expect(entry.pipelineCodedCount).toBe(0);
  });

  it("skips review rows that are missing part of the coding", () => {
    const incomplete: AirtableRecord<ReviewFields> = {
      id: "broken",
      createdTime: "2026-01-01T00:00:00.000Z",
      fields: { Reviewer: "alice", Field: "entity" },
    };
    const entry = entryFor(
      [risk("r1")],
      new Set(["r1"]),
      new Map([["r1", [...fullCoding("alice"), incomplete]]]),
    );
    expect(entry.reviewerCodedCount).toBe(1);
  });

  it("counts nothing for a paper with no risks", () => {
    const entry = entryFor([], new Set(), new Map());
    expect(entry.codableCount).toBe(0);
    expect(entry.reviewerCodedCount).toBe(0);
    expect(entry.pipelineCodedCount).toBe(0);
    expect(entry.state).toBe("awaiting-extraction");
  });
});

describe("buildEntry paper fields", () => {
  it("carries the paper's own details across", () => {
    const entry = entryFor([], new Set(), new Map(), {
      Title: ["A paper about risk"],
      ClassificationReviewer: { id: "usr1", name: "Alice A" },
      ClassificationProgress: "In Progress",
    });
    expect(entry.quickRef).toBe(QUICK_REF);
    expect(entry.title).toBe("A paper about risk");
    expect(entry.assignee).toBe("Alice A");
    expect(entry.progress).toBe("In Progress");
  });

  it("reports missing details as null rather than undefined", () => {
    const entry = entryFor([], new Set(), new Map());
    expect(entry.title).toBeNull();
    expect(entry.assignee).toBeNull();
    expect(entry.progress).toBeNull();
  });

  it("reports a collaborator with no name as unassigned", () => {
    const entry = entryFor([], new Set(), new Map(), {
      ClassificationReviewer: { id: "usr1" },
    });
    expect(entry.assignee).toBeNull();
  });
});

describe("groupRisksByPaper", () => {
  it("groups risks under their quick ref", () => {
    const a: AirtableRecord<RiskFields> = {
      id: "r1",
      createdTime: "t",
      fields: { QuickRef: "Lee2025" },
    };
    const b: AirtableRecord<RiskFields> = {
      id: "r2",
      createdTime: "t",
      fields: { QuickRef: "Roe2025" },
    };
    const c: AirtableRecord<RiskFields> = {
      id: "r3",
      createdTime: "t",
      fields: { QuickRef: "Lee2025" },
    };
    const grouped = groupRisksByPaper([a, b, c]);
    expect(grouped.get("Lee2025")?.map((r) => r.id)).toEqual(["r1", "r3"]);
    expect(grouped.get("Roe2025")?.map((r) => r.id)).toEqual(["r2"]);
  });

  it("refuses a risk that belongs to no paper", () => {
    const orphan: AirtableRecord<RiskFields> = {
      id: "r1",
      createdTime: "t",
      fields: {},
    };
    expect(() => groupRisksByPaper([orphan])).toThrow("r1");
  });
});

describe("requiredQuickRef", () => {
  it("returns the quick ref when there is one", () => {
    expect(
      requiredQuickRef({
        id: "r1",
        createdTime: "t",
        fields: { QuickRef: QUICK_REF },
      }),
    ).toBe(QUICK_REF);
  });

  it("names the offending record when the quick ref is missing", () => {
    expect(() =>
      requiredQuickRef({ id: "recBad", createdTime: "t", fields: {} }),
    ).toThrow("recBad");
  });

  it("treats a blank quick ref as missing", () => {
    for (const QuickRef of ["", "   "]) {
      expect(() =>
        requiredQuickRef({
          id: "recBad",
          createdTime: "t",
          fields: { QuickRef },
        }),
      ).toThrow("recBad");
    }
  });
});
