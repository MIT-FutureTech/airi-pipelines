import { describe, expect, it } from "vitest";
import { emptyJudgement, parseDecision } from "@/lib/judgements";

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
