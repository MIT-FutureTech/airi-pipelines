import { describe, expect, it } from "vitest";
import { cellKey } from "@/lib/cells";
import {
  emptyJudgement,
  judgementsByCell,
  parseDecision,
} from "@/lib/judgements";

describe("parseDecision", () => {
  it("accepts a decision", () => {
    expect(parseDecision("unsure")).toBe("unsure");
  });

  it("rejects anything else", () => {
    expect(() => parseDecision("maybe")).toThrow("Unknown decision maybe");
  });
});

describe("emptyJudgement", () => {
  it("starts with nothing decided", () => {
    expect(emptyJudgement("recBank", "recDomain22")).toEqual({
      companyId: "recBank",
      codeRecordId: "recDomain22",
      decision: null,
      comment: "",
      supportingMitigationRecordIds: [],
    });
  });
});

describe("judgementsByCell", () => {
  it("finds each judgement by its company and code", () => {
    const bank = {
      ...emptyJudgement("recBank", "recDomain22"),
      decision: "yes" as const,
    };
    const retail = emptyJudgement("recRetail", "recModelCards");

    expect(judgementsByCell([bank, retail])).toEqual(
      new Map([
        [cellKey("recBank", "recDomain22"), bank],
        [cellKey("recRetail", "recModelCards"), retail],
      ]),
    );
  });
});
