import type { WorkerEnv } from "@api/_env";
import handler from "@api/judgements";
import { afterEach, describe, expect, it, vi } from "vitest";

const ENV: WorkerEnv = {
  AIRTABLE_PAT: "pat-test",
  AIRTABLE_BASE_ID: "appTest",
  AIRTABLE_JUDGEMENTS_TABLE: "Mitigation Judgements",
};

function get(headers: Record<string, string>): Request {
  return new Request("https://reviewer.example.com/api/judgements", {
    headers,
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("GET /api/judgements", () => {
  it("lists the signed-in user's judgements", async () => {
    const urls: URL[] = [];
    vi.stubGlobal("fetch", (input: string) => {
      urls.push(new URL(input));
      return Promise.resolve(
        Response.json({
          records: [
            {
              id: "recJudgement",
              createdTime: "2026-11-22T00:00:00.000Z",
              fields: {
                Company: ["recBank"],
                Code: ["recDomain22"],
                Decision: "Yes",
              },
            },
          ],
        }),
      );
    });

    const response = await handler(
      get({ "Cf-Access-Authenticated-User-Email": "someone@example.com" }),
      ENV,
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      judgements: [
        {
          companyId: "recBank",
          codeRecordId: "recDomain22",
          decision: "yes",
          comment: "",
          supportingMitigationRecordIds: [],
        },
      ],
    });
    expect(urls[0].searchParams.get("filterByFormula")).toBe(
      '{Reviewer}="someone@example.com"',
    );
  });

  it("refuses a request without a signed-in user", async () => {
    const response = await handler(get({}), ENV);

    expect(response.status).toBe(401);
  });

  it("refuses other methods", async () => {
    const request = new Request("https://reviewer.example.com/api/judgements", {
      method: "DELETE",
    });

    const response = await handler(request, ENV);

    expect(response.status).toBe(405);
  });
});

describe("PUT /api/judgements", () => {
  function put(body: unknown): Request {
    return new Request("https://reviewer.example.com/api/judgements", {
      method: "PUT",
      headers: { "Cf-Access-Authenticated-User-Email": "someone@example.com" },
      body: JSON.stringify(body),
    });
  }

  it("saves the judgement under the user's key", async () => {
    const bodies: unknown[] = [];
    vi.stubGlobal("fetch", (_input: string, init: RequestInit) => {
      const sent = JSON.parse(String(init.body));
      bodies.push(sent);
      return Promise.resolve(
        Response.json({
          records: [
            {
              id: "recJudgement",
              createdTime: "2026-11-22T00:00:00.000Z",
              fields: sent.records[0].fields,
            },
          ],
        }),
      );
    });

    const response = await handler(
      put({
        companyId: "recBank",
        companyName: "Example Bank",
        codeRecordId: "recDomain22",
        codeKey: "Domain 2.2",
        decision: "yes",
        comment: "",
        supportingMitigationRecordIds: ["recMitigation"],
      }),
      ENV,
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      companyId: "recBank",
      codeRecordId: "recDomain22",
      decision: "yes",
      comment: "",
      supportingMitigationRecordIds: ["recMitigation"],
    });
    expect(bodies).toEqual([
      {
        performUpsert: { fieldsToMergeOn: ["Key"] },
        records: [
          {
            fields: {
              Key: "Example Bank · Domain 2.2 · someone@example.com",
              Company: ["recBank"],
              Code: ["recDomain22"],
              Reviewer: "someone@example.com",
              Decision: "Yes",
              Comment: "",
              "Supporting mitigations": ["recMitigation"],
            },
          },
        ],
      },
    ]);
  });

  it("refuses a judgement it can't read", async () => {
    const response = await handler(put({ decision: "yes" }), ENV);

    expect(response.status).toBe(400);
  });
});
