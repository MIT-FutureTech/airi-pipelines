import { describe, expect, it } from "vitest";
import { codeGroups, fullLabel, parseTaxonomy, shortLabel } from "@/lib/codes";
import type { Code, Taxonomy } from "@/lib/types";

function code(
  taxonomy: Taxonomy,
  order: number,
  group: string | null,
  number: string | null,
): Code {
  return {
    record_id: `rec${taxonomy}${order}`,
    key: `${taxonomy} ${number ?? order}`,
    taxonomy,
    code: number,
    name: `${taxonomy} number ${order}`,
    short_name: number === null ? null : `Short ${order}`,
    group,
    order,
    definition: "...",
    details: null,
  };
}

describe("codeGroups", () => {
  it("groups a taxonomy's codes in order", () => {
    const second = code("Domain", 2, "AI System", "1.2");
    const first = code("Domain", 1, "AI System", "1.1");
    const third = code("Domain", 3, "Ecosystem", "3.1");
    const practice = code("Practice", 1, null, null);

    expect(codeGroups([third, second, practice, first], "Domain")).toEqual([
      { name: "AI System", codes: [first, second] },
      { name: "Ecosystem", codes: [third] },
    ]);
  });

  it("puts ungrouped practices in one group", () => {
    const first = code("Practice", 1, null, null);
    const second = code("Practice", 2, null, null);

    expect(codeGroups([second, first], "Practice")).toEqual([
      { name: null, codes: [first, second] },
    ]);
  });
});

describe("labels", () => {
  it("label a code by its number and name", () => {
    const domain = code("Domain", 1, "AI System", "1.1");

    expect(shortLabel(domain)).toBe("1.1 Short 1");
    expect(fullLabel(domain)).toBe("1.1 Domain number 1");
  });

  it("label a practice by its name alone", () => {
    const practice = code("Practice", 4, null, null);

    expect(shortLabel(practice)).toBe("Practice number 4");
    expect(fullLabel(practice)).toBe("Practice number 4");
  });
});

describe("parseTaxonomy", () => {
  it("accepts a taxonomy", () => {
    expect(parseTaxonomy("Instrument")).toBe("Instrument");
  });

  it("rejects anything else", () => {
    expect(() => parseTaxonomy("Locus")).toThrow("Unknown taxonomy Locus");
  });
});
