import { AirtableError } from "@api/_airtable";
import { handleError } from "@api/_http";
import { describe, expect, it } from "vitest";

describe("handleError", () => {
  it("reports an Airtable failure as a bad gateway", async () => {
    const response = handleError(new AirtableError(422, "INVALID_VALUE"));

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({
      error: "Airtable request failed",
      detail: "INVALID_VALUE",
    });
  });

  it("reports anything else as a server error", async () => {
    const response = handleError(new Error("Missing setting"));

    expect(response.status).toBe(500);
    expect(await response.json()).toEqual({ error: "Missing setting" });
  });
});
