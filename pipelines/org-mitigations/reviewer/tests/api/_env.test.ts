import { readAirtableEnv } from "@api/_env";
import { describe, expect, it } from "vitest";

describe("readAirtableEnv", () => {
  it("reads every setting", () => {
    expect(
      readAirtableEnv({
        AIRTABLE_PAT: "pat-test",
        AIRTABLE_BASE_ID: "appTest",
        AIRTABLE_JUDGEMENTS_TABLE: "Mitigation Judgements",
      }),
    ).toEqual({
      pat: "pat-test",
      baseId: "appTest",
      judgementsTable: "Mitigation Judgements",
    });
  });

  it("refuses a blank setting", () => {
    expect(() =>
      readAirtableEnv({
        AIRTABLE_PAT: "",
        AIRTABLE_BASE_ID: "appTest",
        AIRTABLE_JUDGEMENTS_TABLE: "Mitigation Judgements",
      }),
    ).toThrow("Missing required environment variable: AIRTABLE_PAT");
  });
});
