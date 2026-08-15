import {
  AirtableError,
  createRecord,
  createRecords,
  deleteRecords,
  escapeFormulaString,
  getRecord,
  listAllRecords,
  listAllRecordsSharded,
  type ShardKey,
  updateRecord,
  updateRecords,
} from "@api/_airtable";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const PAT = "pat-test";
const BASE = "appTest";
const TABLE = "Reviews";

interface Call {
  url: URL;
  init: RequestInit | undefined;
}

interface Reply {
  status: number;
  body?: unknown;
  retryAfter?: string;
}

let calls: Call[];

// The final reply repeats, so a single failing reply models "fails forever".
function stubFetch(replies: Reply[]): void {
  let index = 0;
  vi.stubGlobal("fetch", (input: string, init?: RequestInit) => {
    calls.push({ url: new URL(input), init });
    const reply = replies[Math.min(index, replies.length - 1)];
    index += 1;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (reply.retryAfter !== undefined) {
      headers["retry-after"] = reply.retryAfter;
    }
    return Promise.resolve(
      new Response(JSON.stringify(reply.body ?? {}), {
        status: reply.status,
        headers,
      }),
    );
  });
}

function page(ids: string[], offset?: string): Reply {
  return {
    status: 200,
    body: {
      records: ids.map((id) => ({
        id,
        createdTime: "2026-01-01T00:00:00.000Z",
        fields: { Name: id },
      })),
      offset,
    },
  };
}

// Replaces the backoff wait with an immediate one, recording what was asked for.
function recordDelays(): number[] {
  const delays: number[] = [];
  const realSetTimeout = setTimeout;
  vi.stubGlobal("setTimeout", (fn: () => void, ms?: number) => {
    delays.push(ms ?? 0);
    return realSetTimeout(fn, 0);
  });
  return delays;
}

function formulaOf(call: Call): string | null {
  return call.url.searchParams.get("filterByFormula");
}

beforeEach(() => {
  calls = [];
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("escapeFormulaString", () => {
  it("leaves an ordinary string alone", () => {
    expect(escapeFormulaString("Lee2025")).toBe("Lee2025");
    expect(escapeFormulaString("")).toBe("");
  });

  it("escapes quotes and backslashes", () => {
    expect(escapeFormulaString('say "hi"')).toBe('say \\"hi\\"');
    expect(escapeFormulaString("a\\b")).toBe("a\\\\b");
  });

  it("escapes backslashes before quotes, so an escaped quote survives", () => {
    expect(escapeFormulaString('a\\"b')).toBe('a\\\\\\"b');
  });
});

describe("listAllRecords request shape", () => {
  it("asks for a full page and authenticates", async () => {
    stubFetch([page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(calls[0].url.searchParams.get("pageSize")).toBe("100");
    expect(calls[0].url.pathname).toBe(`/v0/${BASE}/${TABLE}`);
    const headers = calls[0].init?.headers as Record<string, string>;
    expect(headers.Authorization).toBe(`Bearer ${PAT}`);
  });

  it("sends no offset on the first request", async () => {
    stubFetch([page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(calls[0].url.searchParams.has("offset")).toBe(false);
  });

  it("encodes a table name containing spaces", async () => {
    stubFetch([page([])]);
    await listAllRecords(PAT, BASE, "Proposed Extractions");
    expect(calls[0].url.pathname).toBe(`/v0/${BASE}/Proposed%20Extractions`);
  });

  it("passes the view, formula, page size, and fields through", async () => {
    stubFetch([page([])]);
    await listAllRecords(PAT, BASE, TABLE, {
      view: "Grid",
      filterByFormula: '{Reviewer}="alice"',
      pageSize: 50,
      fields: ["Reviewer", "Field"],
    });
    const params = calls[0].url.searchParams;
    expect(params.get("view")).toBe("Grid");
    expect(params.get("filterByFormula")).toBe('{Reviewer}="alice"');
    expect(params.get("pageSize")).toBe("50");
    expect(params.getAll("fields[]")).toEqual(["Reviewer", "Field"]);
  });

  it("omits the view and formula when they are not given", async () => {
    stubFetch([page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(calls[0].url.searchParams.has("view")).toBe(false);
    expect(calls[0].url.searchParams.has("filterByFormula")).toBe(false);
  });
});

describe("listAllRecords pagination", () => {
  it("follows every offset and returns the pages in order", async () => {
    stubFetch([
      page(["rec1", "rec2"], "off1"),
      page(["rec3"], "off2"),
      page(["rec4"]),
    ]);
    const records = await listAllRecords(PAT, BASE, TABLE);
    expect(records.map((r) => r.id)).toEqual(["rec1", "rec2", "rec3", "rec4"]);
    expect(calls).toHaveLength(3);
    expect(calls[1].url.searchParams.get("offset")).toBe("off1");
    expect(calls[2].url.searchParams.get("offset")).toBe("off2");
  });

  it("stops as soon as a page carries no offset", async () => {
    stubFetch([page(["rec1"])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(calls).toHaveLength(1);
  });

  it("returns nothing for an empty table", async () => {
    stubFetch([page([])]);
    expect(await listAllRecords(PAT, BASE, TABLE)).toEqual([]);
  });

  it("repeats the caller's options on later pages", async () => {
    stubFetch([page(["rec1"], "off1"), page(["rec2"])]);
    await listAllRecords(PAT, BASE, TABLE, {
      filterByFormula: '{Reviewer}="alice"',
      fields: ["Reviewer"],
    });
    expect(formulaOf(calls[1])).toBe('{Reviewer}="alice"');
    expect(calls[1].url.searchParams.getAll("fields[]")).toEqual(["Reviewer"]);
  });
});

describe("listAllRecordsSharded", () => {
  const shard: ShardKey = { field: "RiskReviewId", count: 4 };

  it("partitions the table exhaustively and without overlap", async () => {
    stubFetch([page([])]);
    await listAllRecordsSharded(PAT, BASE, TABLE, {}, shard);
    expect(calls).toHaveLength(4);
    expect(calls.map(formulaOf).sort()).toEqual([
      "MOD({RiskReviewId}, 4)=0",
      "MOD({RiskReviewId}, 4)=1",
      "MOD({RiskReviewId}, 4)=2",
      "MOD({RiskReviewId}, 4)=3",
    ]);
  });

  it("keeps the caller's filter alongside the partition", async () => {
    stubFetch([page([])]);
    await listAllRecordsSharded(
      PAT,
      BASE,
      TABLE,
      { filterByFormula: '{Reviewer}="alice"' },
      shard,
    );
    for (const call of calls) {
      expect(formulaOf(call)).toMatch(
        /^AND\(MOD\(\{RiskReviewId\}, 4\)=[0-3], \{Reviewer\}="alice"\)$/,
      );
    }
  });

  it("gathers the records from every shard", async () => {
    stubFetch([page(["rec1"])]);
    const records = await listAllRecordsSharded(PAT, BASE, TABLE, {}, shard);
    expect(records).toHaveLength(4);
  });

  it("passes the other options to every shard", async () => {
    stubFetch([page([])]);
    await listAllRecordsSharded(
      PAT,
      BASE,
      TABLE,
      { fields: ["Reviewer"], pageSize: 50 },
      shard,
    );
    for (const call of calls) {
      expect(call.url.searchParams.getAll("fields[]")).toEqual(["Reviewer"]);
      expect(call.url.searchParams.get("pageSize")).toBe("50");
    }
  });

  it("issues one request per shard when the count changes", async () => {
    stubFetch([page([])]);
    await listAllRecordsSharded(
      PAT,
      BASE,
      TABLE,
      {},
      { field: "RiskReviewId", count: 2 },
    );
    expect(calls.map(formulaOf).sort()).toEqual([
      "MOD({RiskReviewId}, 2)=0",
      "MOD({RiskReviewId}, 2)=1",
    ]);
  });
});

describe("rate limit handling", () => {
  it("retries after a 429 and returns the records that follow", async () => {
    recordDelays();
    stubFetch([{ status: 429 }, page(["rec1"])]);
    const records = await listAllRecords(PAT, BASE, TABLE);
    expect(records.map((r) => r.id)).toEqual(["rec1"]);
    expect(calls).toHaveLength(2);
  });

  it("backs off exponentially when no retry-after is offered", async () => {
    const delays = recordDelays();
    stubFetch([{ status: 429 }, { status: 429 }, { status: 429 }, page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(delays).toEqual([250, 500, 1000]);
  });

  it("honours a retry-after header, in seconds", async () => {
    const delays = recordDelays();
    stubFetch([{ status: 429, retryAfter: "1" }, page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(delays).toEqual([1000]);
  });

  it("caps a long retry-after", async () => {
    const delays = recordDelays();
    stubFetch([{ status: 429, retryAfter: "30" }, page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(delays).toEqual([2000]);
  });

  it("ignores an unusable retry-after and backs off instead", async () => {
    const delays = recordDelays();
    stubFetch([{ status: 429, retryAfter: "soon" }, page([])]);
    await listAllRecords(PAT, BASE, TABLE);
    expect(delays).toEqual([250]);
  });

  it("gives up after three retries", async () => {
    recordDelays();
    stubFetch([{ status: 429 }]);
    await expect(listAllRecords(PAT, BASE, TABLE)).rejects.toBeInstanceOf(
      AirtableError,
    );
    expect(calls).toHaveLength(4);
  });

  it("does not retry an error that is not a rate limit", async () => {
    recordDelays();
    stubFetch([{ status: 500 }]);
    await expect(listAllRecords(PAT, BASE, TABLE)).rejects.toBeInstanceOf(
      AirtableError,
    );
    expect(calls).toHaveLength(1);
  });

  it("retries writes too", async () => {
    recordDelays();
    stubFetch([{ status: 429 }, { status: 200, body: { records: [] } }]);
    await createRecords(PAT, BASE, TABLE, [{ Name: "A" }]);
    expect(calls).toHaveLength(2);
  });
});

describe("AirtableError", () => {
  it("carries the status and body of the failed request", async () => {
    stubFetch([{ status: 422, body: { error: "Unknown field names" } }]);
    const error = await listAllRecords(PAT, BASE, TABLE).catch((e) => e);
    expect(error).toBeInstanceOf(AirtableError);
    expect(error.status).toBe(422);
    expect(error.body).toContain("Unknown field names");
    expect(error.message).toContain("422");
  });
});

describe("getRecord", () => {
  it("fetches one record by id", async () => {
    stubFetch([
      {
        status: 200,
        body: { id: "rec1", createdTime: "t", fields: { Name: "A" } },
      },
    ]);
    const record = await getRecord(PAT, BASE, TABLE, "rec1");
    expect(record.id).toBe("rec1");
    expect(calls[0].url.pathname).toBe(`/v0/${BASE}/${TABLE}/rec1`);
  });
});

describe("createRecords and updateRecords", () => {
  it("posts new rows wrapped in a fields object", async () => {
    stubFetch([{ status: 200, body: { records: [] } }]);
    await createRecords(PAT, BASE, TABLE, [{ Name: "A" }, { Name: "B" }]);
    expect(calls[0].init?.method).toBe("POST");
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({
      records: [{ fields: { Name: "A" } }, { fields: { Name: "B" } }],
    });
  });

  it("patches existing rows by id", async () => {
    stubFetch([{ status: 200, body: { records: [] } }]);
    await updateRecords(PAT, BASE, TABLE, [
      { id: "rec1", fields: { Name: "A" } },
    ]);
    expect(calls[0].init?.method).toBe("PATCH");
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({
      records: [{ id: "rec1", fields: { Name: "A" } }],
    });
  });

  it("sends no request at all for an empty write", async () => {
    stubFetch([{ status: 200, body: { records: [] } }]);
    expect(await createRecords(PAT, BASE, TABLE, [])).toEqual([]);
    expect(await updateRecords(PAT, BASE, TABLE, [])).toEqual([]);
    expect(calls).toHaveLength(0);
  });

  it("returns the single record for the singular helpers", async () => {
    stubFetch([
      {
        status: 200,
        body: { records: [{ id: "rec1", createdTime: "t", fields: {} }] },
      },
    ]);
    expect((await createRecord(PAT, BASE, TABLE, { Name: "A" })).id).toBe(
      "rec1",
    );
    expect(
      (await updateRecord(PAT, BASE, TABLE, "rec1", { Name: "A" })).id,
    ).toBe("rec1");
  });
});

describe("deleteRecords", () => {
  it("lists every id as a repeated query parameter", async () => {
    stubFetch([{ status: 200, body: {} }]);
    await deleteRecords(PAT, BASE, TABLE, ["rec1", "rec2"]);
    expect(calls[0].init?.method).toBe("DELETE");
    expect(calls[0].url.searchParams.getAll("records[]")).toEqual([
      "rec1",
      "rec2",
    ]);
  });

  it("sends no request when there is nothing to delete", async () => {
    stubFetch([{ status: 200, body: {} }]);
    await deleteRecords(PAT, BASE, TABLE, []);
    expect(calls).toHaveLength(0);
  });
});
