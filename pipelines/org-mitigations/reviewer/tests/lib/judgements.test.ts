import { describe, expect, it } from "vitest";
import { cellKey } from "@/lib/cells";
import {
  emptyJudgement,
  judgementsByCell,
  parseDecision,
  saveRequest,
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

describe("saveRequest", () => {
  it("adds the names the saved judgement's key needs", () => {
    expect(
      saveRequest(
        emptyJudgement("recBank", "recDomain22"),
        "Example Bank",
        "Domain 2.2",
      ),
    ).toEqual({
      companyId: "recBank",
      companyName: "Example Bank",
      codeRecordId: "recDomain22",
      codeKey: "Domain 2.2",
      decision: null,
      comment: "",
      supportingMitigationRecordIds: [],
    });
  });
});
