import type { AirtableRecord } from "@api/_airtable";
import { codableIds, isRejected, parentId } from "@api/_tree";
import {
  REJECTED_ORIGIN,
  type RiskFields,
  type RiskOrigin,
} from "@shared/classification";
import { describe, expect, it } from "vitest";

const APPROVED: RiskOrigin = "model-added, human-approved";

function risk(
  id: string,
  parent: string | null,
  origin: RiskOrigin,
): AirtableRecord<RiskFields> {
  return {
    id,
    createdTime: "2026-01-01T00:00:00.000Z",
    fields: {
      Origin: origin,
      Parent: parent === null ? undefined : [parent],
    },
  };
}

describe("isRejected", () => {
  it("is true only for the rejected origin", () => {
    expect(isRejected(risk("a", null, REJECTED_ORIGIN))).toBe(true);
    expect(isRejected(risk("a", null, APPROVED))).toBe(false);
    expect(isRejected(risk("a", null, "human-added"))).toBe(false);
    expect(isRejected(risk("a", null, "model-added, human-edited"))).toBe(
      false,
    );
  });
});

describe("parentId", () => {
  it("reads the first linked parent", () => {
    expect(parentId(risk("a", "b", APPROVED))).toBe("b");
  });

  it("is null when the risk has no parent", () => {
    expect(parentId(risk("a", null, APPROVED))).toBeNull();
  });

  it("is null when the link field is present but empty", () => {
    const orphan: AirtableRecord<RiskFields> = {
      id: "a",
      createdTime: "2026-01-01T00:00:00.000Z",
      fields: { Origin: APPROVED, Parent: [] },
    };
    expect(parentId(orphan)).toBeNull();
  });
});

describe("codableIds", () => {
  it("returns nothing for an empty tree", () => {
    expect(codableIds([])).toEqual(new Set());
  });

  it("treats every risk in a flat list as codable", () => {
    const risks = [
      risk("a", null, APPROVED),
      risk("b", null, APPROVED),
      risk("c", null, "human-added"),
    ];
    expect(codableIds(risks)).toEqual(new Set(["a", "b", "c"]));
  });

  it("excludes a parent that still has surviving children", () => {
    const risks = [
      risk("parent", null, APPROVED),
      risk("child1", "parent", APPROVED),
      risk("child2", "parent", APPROVED),
    ];
    expect(codableIds(risks)).toEqual(new Set(["child1", "child2"]));
  });

  it("excludes rejected leaves", () => {
    const risks = [
      risk("parent", null, APPROVED),
      risk("kept", "parent", APPROVED),
      risk("dropped", "parent", REJECTED_ORIGIN),
    ];
    expect(codableIds(risks)).toEqual(new Set(["kept"]));
  });

  it("promotes a parent whose every child was rejected", () => {
    const risks = [
      risk("parent", null, APPROVED),
      risk("dropped1", "parent", REJECTED_ORIGIN),
      risk("dropped2", "parent", REJECTED_ORIGIN),
    ];
    expect(codableIds(risks)).toEqual(new Set(["parent"]));
  });

  it("keeps a parent non-codable when only some children were rejected", () => {
    const risks = [
      risk("parent", null, APPROVED),
      risk("kept", "parent", APPROVED),
      risk("dropped", "parent", REJECTED_ORIGIN),
    ];
    expect(codableIds(risks)).toEqual(new Set(["kept"]));
  });

  it("takes only the leaves of a deep chain", () => {
    const risks = [
      risk("grandparent", null, APPROVED),
      risk("parent", "grandparent", APPROVED),
      risk("leaf", "parent", APPROVED),
    ];
    expect(codableIds(risks)).toEqual(new Set(["leaf"]));
  });

  it("returns nothing when every risk was rejected", () => {
    const risks = [
      risk("parent", null, REJECTED_ORIGIN),
      risk("child", "parent", REJECTED_ORIGIN),
    ];
    expect(codableIds(risks)).toEqual(new Set());
  });

  it("raises a child past its rejected parent to the surviving ancestor", () => {
    const risks = [
      risk("grandparent", null, APPROVED),
      risk("parent", "grandparent", REJECTED_ORIGIN),
      risk("leaf", "parent", APPROVED),
    ];
    expect(codableIds(risks)).toEqual(new Set(["leaf"]));
  });

  it("walks through a run of rejected ancestors", () => {
    const risks = [
      risk("root", null, APPROVED),
      risk("mid1", "root", REJECTED_ORIGIN),
      risk("mid2", "mid1", REJECTED_ORIGIN),
      risk("leaf", "mid2", APPROVED),
    ];
    expect(codableIds(risks)).toEqual(new Set(["leaf"]));
  });

  it("treats a risk whose parent record is absent as a root", () => {
    const risks = [risk("orphan", "missing", APPROVED)];
    expect(codableIds(risks)).toEqual(new Set(["orphan"]));
  });

  it("terminates on a cycle among rejected ancestors", () => {
    const risks = [
      risk("a", "b", REJECTED_ORIGIN),
      risk("b", "a", REJECTED_ORIGIN),
      risk("leaf", "a", APPROVED),
    ];
    expect(codableIds(risks)).toEqual(new Set(["leaf"]));
  });
});
