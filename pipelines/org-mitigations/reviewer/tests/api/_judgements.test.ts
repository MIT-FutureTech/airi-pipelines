import type { AirtableRecord } from "@api/_airtable";
import { type JudgementFields, readJudgement } from "@api/_judgements";
import { describe, expect, it } from "vitest";

function record(fields: JudgementFields): AirtableRecord<JudgementFields> {
  return {
    id: "recJudgement",
    createdTime: "2026-11-22T00:00:00.000Z",
    fields,
  };
}

describe("readJudgement", () => {
  it("reads every field", () => {
    expect(
      readJudgement(
        record({
          Company: ["recBank"],
          Code: ["recDomain22"],
          Decision: "Unsure",
          Comment: "Only a mention.",
          "Supporting mitigations": ["recMitigation"],
        }),
      ),
    ).toEqual({
      companyId: "recBank",
      codeRecordId: "recDomain22",
      decision: "unsure",
      comment: "Only a mention.",
      supportingMitigationRecordIds: ["recMitigation"],
    });
  });

  it("reads empty fields, which Airtable leaves out", () => {
    expect(
      readJudgement(record({ Company: ["recBank"], Code: ["recDomain22"] })),
    ).toEqual({
      companyId: "recBank",
      codeRecordId: "recDomain22",
      decision: null,
      comment: "",
      supportingMitigationRecordIds: [],
    });
  });

  it("refuses a judgement without a company", () => {
    expect(() => readJudgement(record({ Code: ["recDomain22"] }))).toThrow(
      "Judgement recJudgement should link to one Company, not 0",
    );
  });

  it("refuses a decision it doesn't know", () => {
    expect(() =>
      readJudgement(
        record({
          Company: ["recBank"],
          Code: ["recDomain22"],
          Decision: "Maybe",
        }),
      ),
    ).toThrow("Unknown decision Maybe");
  });
});
