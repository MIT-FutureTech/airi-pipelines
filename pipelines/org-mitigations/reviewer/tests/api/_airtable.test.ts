import {
  AirtableError,
  escapeFormulaString,
  listAllRecords,
  upsertRecord,
} from "@api/_airtable";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const PAT = "pat-test";
const BASE = "appTest";
const TABLE = "Mitigation Judgements";

interface Call {
  url: URL;
  init: RequestInit | undefined;
}

interface Reply {
  status: number;
  body: unknown;
}

let calls: Call[];

function stubFetch(replies: Reply[]): void {
  let index = 0;
  vi.stubGlobal("fetch", (input: string, init?: RequestInit) => {
    calls.push({ url: new URL(input), init });
    const reply = replies[index];
    index += 1;
    return Promise.resolve(
      new Response(JSON.stringify(reply.body), {
        status: reply.status,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function record(id: string): object {
  return { id, createdTime: "2026-11-22T00:00:00.000Z", fields: { Key: id } };
}

beforeEach(() => {
  calls = [];
  vi.stubGlobal("setTimeout", (callback: () => void) => {
    callback();
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("listAllRecords", () => {
  it("follows offsets until the last page", async () => {
    stubFetch([
      { status: 200, body: { records: [record("recA")], offset: "next" } },
      { status: 200, body: { records: [record("recB")] } },
    ]);

    const records = await listAllRecords(PAT, BASE, TABLE, {
      filterByFormula: '{Reviewer}="someone@example.com"',
      fields: ["Key", "Decision"],
    });

    expect(records.map((item) => item.id)).toEqual(["recA", "recB"]);
    expect(calls[0].url.pathname).toBe("/v0/appTest/Mitigation%20Judgements");
    expect(calls[0].url.searchParams.get("filterByFormula")).toBe(
      '{Reviewer}="someone@example.com"',
    );
    expect(calls[0].url.searchParams.getAll("fields[]")).toEqual([
      "Key",
      "Decision",
    ]);
    expect(calls[0].url.searchParams.has("offset")).toBe(false);
    expect(calls[1].url.searchParams.get("offset")).toBe("next");
  });

  it("retries when Airtable limits the rate", async () => {
    stubFetch([
      { status: 429, body: {} },
      { status: 200, body: { records: [record("recA")] } },
    ]);
    vi.spyOn(console, "warn").mockImplementation(() => undefined);

    const records = await listAllRecords(PAT, BASE, TABLE, {});

    expect(records.map((item) => item.id)).toEqual(["recA"]);
    expect(calls).toHaveLength(2);
  });

  it("throws Airtable's reply when a request fails", async () => {
    stubFetch([{ status: 403, body: { error: "NOT_AUTHORIZED" } }]);

    await expect(listAllRecords(PAT, BASE, TABLE, {})).rejects.toThrow(
      AirtableError,
    );
  });
});

describe("upsertRecord", () => {
  it("asks Airtable to merge on the given fields", async () => {
    stubFetch([{ status: 200, body: { records: [record("recA")] } }]);

    const saved = await upsertRecord(PAT, BASE, TABLE, ["Key"], {
      Key: "recA",
    });

    expect(saved.id).toBe("recA");
    expect(calls[0].init?.method).toBe("PATCH");
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({
      performUpsert: { fieldsToMergeOn: ["Key"] },
      records: [{ fields: { Key: "recA" } }],
    });
  });
});

describe("escapeFormulaString", () => {
  it("escapes backslashes before quotes", () => {
    expect(escapeFormulaString('a\\"b')).toBe('a\\\\\\"b');
  });
});
