import type { AirtableRecord } from "@api/_airtable";
import {
  type JudgementFields,
  judgementFields,
  parseSaveRequest,
  readJudgement,
} from "@api/_judgements";
import type { SaveJudgementRequest } from "@shared/judgements";
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

const SAVE: SaveJudgementRequest = {
  companyId: "recBank",
  companyName: "Example Bank",
  codeRecordId: "recDomain22",
  codeKey: "Domain 2.2",
  decision: "no",
  comment: "Only a mention.",
  supportingMitigationRecordIds: ["recMitigation"],
};

describe("judgementFields", () => {
  it("keys the judgement by company, code and user", () => {
    expect(judgementFields(SAVE, "someone@example.com")).toEqual({
      Key: "Example Bank · Domain 2.2 · someone@example.com",
      Company: ["recBank"],
      Code: ["recDomain22"],
      Reviewer: "someone@example.com",
      Decision: "No",
      Comment: "Only a mention.",
      "Supporting mitigations": ["recMitigation"],
    });
  });

  it("clears the decision when there isn't one", () => {
    expect(
      judgementFields({ ...SAVE, decision: null }, "someone@example.com")
        .Decision,
    ).toBeNull();
  });
});

describe("parseSaveRequest", () => {
  it("accepts a complete request", () => {
    expect(parseSaveRequest(JSON.parse(JSON.stringify(SAVE)))).toEqual(SAVE);
  });

  it("accepts a request without a decision", () => {
    expect(parseSaveRequest({ ...SAVE, decision: null })).toEqual({
      ...SAVE,
      decision: null,
    });
  });

  it.each([
    ["an unknown decision", { ...SAVE, decision: "maybe" }],
    ["a blank company", { ...SAVE, companyId: "" }],
    ["a missing comment", { ...SAVE, comment: undefined }],
    [
      "a mitigation that isn't an ID",
      { ...SAVE, supportingMitigationRecordIds: [7] },
    ],
    ["something that isn't an object", "judgement"],
  ])("refuses %s", (_description, body) => {
    expect(parseSaveRequest(body)).toBeNull();
  });
});
