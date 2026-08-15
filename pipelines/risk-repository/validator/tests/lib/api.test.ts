import type {
  PapersResponse,
  ReviewField,
  ReviewMode,
  ReviewResponse,
  RiskEntry,
  RiskManifestResponse,
  SaveCodingsRequest,
  SaveCodingsResponse,
} from "@shared/classification";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const QUICK_REF = "Doe2025";
const REVIEWER = "alice";

async function loadApi() {
  vi.resetModules();
  return await import("@/lib/api");
}

function stubFetch(body: (url: URL) => unknown): string[] {
  const calls: string[] = [];
  vi.stubGlobal("fetch", (input: string) => {
    const url = new URL(input, "http://test.local");
    calls.push(url.pathname);
    const payload = body(url);
    if (payload === undefined) {
      return Promise.resolve(new Response("upstream failed", { status: 500 }));
    }
    return Promise.resolve(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
  return calls;
}

function response(
  id: string,
  field: ReviewField,
  value: string,
): ReviewResponse {
  return { id, field, value, mode: "anchored", comment: null };
}

function coded(prefix: string): ReviewResponse[] {
  return [
    response(`${prefix}-entity`, "entity", "human"),
    response(`${prefix}-intent`, "intent", "intentional"),
    response(`${prefix}-timing`, "timing", "pre-deployment"),
    response(`${prefix}-subdomain`, "subdomain", "1.1"),
  ];
}

function riskEntry(
  id: string,
  codable: boolean,
  responses: ReviewResponse[],
): RiskEntry {
  return {
    id,
    readableId: `${QUICK_REF}.${id}`,
    name: `Risk ${id}`,
    parentId: null,
    codable,
    origin: "human-added",
    description: "",
    descriptionPage: null,
    supportingQuote: "",
    additionalEvidence: [],
    responses,
    pipelineResponses: [],
  };
}

// One coded risk out of three codable ones, plus a coded risk that is not
// codable and so must never reach the reviewer's count.
function manifest(mode: ReviewMode): RiskManifestResponse {
  return {
    quickRef: QUICK_REF,
    title: "A paper",
    mode,
    risks: [
      riskEntry("r1", true, []),
      riskEntry("r2", true, coded("r2")),
      riskEntry("r3", true, [response("r3-entity", "entity", "human")]),
      riskEntry("r4", false, coded("r4")),
    ],
  };
}

function papers(): PapersResponse {
  return {
    papers: [
      {
        quickRef: QUICK_REF,
        title: "A paper",
        assignee: REVIEWER,
        progress: "In Progress",
        state: "ready",
        codableCount: 3,
        reviewerCodedCount: 1,
        pipelineCodedCount: 3,
      },
      {
        quickRef: "Roe2025",
        title: "Another paper",
        assignee: REVIEWER,
        progress: null,
        state: "classifying",
        codableCount: 5,
        reviewerCodedCount: 4,
        pipelineCodedCount: 2,
      },
    ],
  };
}

const SAVED: SaveCodingsResponse = { riskId: "r3", responses: coded("new") };

function saveRequest(reviewer: string): SaveCodingsRequest {
  return {
    reviewer,
    riskId: "r3",
    mode: "anchored",
    codings: [],
    staleReviewIds: [],
  };
}

function route(url: URL): unknown {
  if (url.pathname === "/api/papers") {
    return papers();
  }
  if (url.pathname === "/api/risks/manifest") {
    return manifest(url.searchParams.get("mode") as ReviewMode);
  }
  if (url.pathname === "/api/codings") {
    return SAVED;
  }
  return undefined;
}

let calls: string[];

beforeEach(() => {
  calls = stubFetch(route);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("saveCodings cache patching", () => {
  it("updates the saved risk in every cached mode", async () => {
    const api = await loadApi();
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "blind",
    });
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "anchored",
    });
    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));

    for (const mode of ["blind", "anchored"] as const) {
      const patched = await api.getRiskManifest({
        quickRef: QUICK_REF,
        reviewer: REVIEWER,
        mode,
      });
      expect(patched.mode).toBe(mode);
      const saved = patched.risks.find((risk) => risk.id === "r3");
      expect(saved?.responses).toEqual(SAVED.responses);
    }
  });

  it("leaves the other risks in the manifest alone", async () => {
    const api = await loadApi();
    const params = {
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "blind" as const,
    };
    const before = await api.getRiskManifest(params);
    const untouched = before.risks.filter((risk) => risk.id !== "r3");
    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));

    const after = await api.getRiskManifest(params);
    expect(after.risks.filter((risk) => risk.id !== "r3")).toEqual(untouched);
  });

  it("recomputes the reviewer's coded count from the patched manifest", async () => {
    const api = await loadApi();
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "anchored",
    });
    const before = await api.getPapers(REVIEWER);
    expect(before.papers[0].reviewerCodedCount).toBe(1);

    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));

    const after = await api.getPapers(REVIEWER);
    expect(after.papers[0].reviewerCodedCount).toBe(2);
  });

  it("changes nothing else about the paper it patches", async () => {
    const api = await loadApi();
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "anchored",
    });
    await api.getPapers(REVIEWER);
    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));

    const after = await api.getPapers(REVIEWER);
    expect(after.papers[0]).toEqual({
      ...papers().papers[0],
      reviewerCodedCount: 2,
    });
    expect(after.papers[1]).toEqual(papers().papers[1]);
  });

  it("issues no further requests to bring the caches up to date", async () => {
    const api = await loadApi();
    await api.getPapers(REVIEWER);
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "blind",
    });
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "anchored",
    });
    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));
    await api.getPapers(REVIEWER);
    await api.getRiskManifest({
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "blind",
    });

    expect(calls).toEqual([
      "/api/papers",
      "/api/risks/manifest",
      "/api/risks/manifest",
      "/api/codings",
    ]);
  });
});

describe("saveCodings without a manifest to patch", () => {
  it("evicts the paper list so the count is refetched", async () => {
    const api = await loadApi();
    await api.getPapers(REVIEWER);
    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));
    await api.getPapers(REVIEWER);

    expect(calls).toEqual(["/api/papers", "/api/codings", "/api/papers"]);
  });

  it("does nothing when the reviewer has nothing cached", async () => {
    const api = await loadApi();
    await api.getPapers(REVIEWER);
    await api.saveCodings(QUICK_REF, saveRequest("bob"));

    const after = await api.getPapers(REVIEWER);
    expect(after).toEqual(papers());
    expect(calls).toEqual(["/api/papers", "/api/codings"]);
  });
});

describe("saveCodings when the cached manifest failed to load", () => {
  it("keeps the paper list rather than inheriting the failure", async () => {
    vi.unstubAllGlobals();
    calls = stubFetch((url) =>
      url.pathname === "/api/risks/manifest" ? undefined : route(url),
    );
    const api = await loadApi();
    const params = {
      quickRef: QUICK_REF,
      reviewer: REVIEWER,
      mode: "blind" as const,
    };
    await expect(api.getRiskManifest(params)).rejects.toThrow();
    await api.getPapers(REVIEWER);
    await api.saveCodings(QUICK_REF, saveRequest(REVIEWER));

    expect(await api.getPapers(REVIEWER)).toEqual(papers());
    await expect(api.getRiskManifest(params)).rejects.toThrow();
  });
});
