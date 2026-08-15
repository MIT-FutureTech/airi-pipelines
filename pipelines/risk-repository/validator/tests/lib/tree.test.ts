import type { RiskEntry } from "@shared/classification";
import { describe, expect, it } from "vitest";
import { ancestorsOf, depthOf, indexRisks } from "@/lib/tree";

function entry(id: string, parentId: string | null): RiskEntry {
  return {
    id,
    readableId: `Lee2025.${id}`,
    name: `Risk ${id}`,
    parentId,
    codable: true,
    origin: "human-added",
    description: "",
    descriptionPage: null,
    supportingQuote: "",
    additionalEvidence: [],
    responses: [],
    pipelineResponses: [],
  };
}

const ROOT = entry("root", null);
const MIDDLE = entry("middle", "root");
const LEAF = entry("leaf", "middle");
const CHAIN = [ROOT, MIDDLE, LEAF];

describe("indexRisks", () => {
  it("keys every risk by its id", () => {
    const index = indexRisks(CHAIN);
    expect(index.size).toBe(3);
    expect(index.get("middle")).toBe(MIDDLE);
  });

  it("is empty for no risks", () => {
    expect(indexRisks([]).size).toBe(0);
  });
});

describe("ancestorsOf", () => {
  it("finds nothing above a root", () => {
    expect(ancestorsOf(indexRisks(CHAIN), ROOT)).toEqual([]);
  });

  it("finds the parent of a child", () => {
    expect(ancestorsOf(indexRisks(CHAIN), MIDDLE)).toEqual([ROOT]);
  });

  it("returns the whole chain, outermost first", () => {
    expect(ancestorsOf(indexRisks(CHAIN), LEAF)).toEqual([ROOT, MIDDLE]);
  });

  it("stops where the chain leaves the index", () => {
    const orphan = entry("orphan", "missing");
    expect(ancestorsOf(indexRisks([orphan]), orphan)).toEqual([]);
  });

  it("keeps what it found before the chain broke", () => {
    const detached = entry("detached", "gone");
    const child = entry("child", "detached");
    const index = indexRisks([detached, child]);
    expect(ancestorsOf(index, child)).toEqual([detached]);
  });

  it("stops after one pass around a cycle", () => {
    const a = entry("a", "b");
    const b = entry("b", "a");
    const index = indexRisks([a, b]);
    expect(ancestorsOf(index, a)).toEqual([a, b]);
  });
});

describe("depthOf", () => {
  it("counts a root as depth zero", () => {
    expect(depthOf(indexRisks(CHAIN), ROOT)).toBe(0);
  });

  it("counts each step down the chain", () => {
    const index = indexRisks(CHAIN);
    expect(depthOf(index, MIDDLE)).toBe(1);
    expect(depthOf(index, LEAF)).toBe(2);
  });
});
