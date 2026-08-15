import { parseBody } from "@api/codings";
import {
  NOT_A_RISK,
  type ReviewResponse,
  type RiskEntry,
  type SaveCodingsRequest,
} from "@shared/classification";
import { describe, expect, it } from "vitest";
import {
  codingsRequest,
  type Draft,
  draftFromResponses,
  withNotARisk,
  withValue,
} from "@/lib/draft";

function axisResponses(): ReviewResponse[] {
  return [
    {
      id: "r-entity",
      field: "entity",
      value: "human",
      mode: "anchored",
      comment: null,
    },
    {
      id: "r-intent",
      field: "intent",
      value: "intentional",
      mode: "anchored",
      comment: null,
    },
    {
      id: "r-timing",
      field: "timing",
      value: "pre-deployment",
      mode: "anchored",
      comment: null,
    },
    {
      id: "r-subdomain",
      field: "subdomain",
      value: "1.1",
      mode: "anchored",
      comment: null,
    },
  ];
}

function entryWith(responses: ReviewResponse[]): RiskEntry {
  return {
    id: "rec-risk",
    readableId: "Doe2025.01",
    name: "Example risk",
    parentId: null,
    codable: true,
    origin: "human-added",
    description: "",
    descriptionPage: null,
    supportingQuote: "",
    additionalEvidence: [],
    responses,
    pipelineResponses: [],
  };
}

function overTheWire(entry: RiskEntry, draft: Draft): unknown {
  const request = codingsRequest({
    reviewer: "alice",
    mode: "anchored",
    entry,
    draft,
  });
  return JSON.parse(JSON.stringify(request));
}

function validBody(): SaveCodingsRequest {
  return {
    reviewer: "alice",
    riskId: "rec-risk",
    mode: "anchored",
    codings: [
      { reviewId: null, field: "entity", value: "human", comment: null },
      {
        reviewId: "r-intent",
        field: "intent",
        value: "intentional",
        comment: "why",
      },
    ],
    staleReviewIds: ["r-old"],
  };
}

function withField(field: string, value: unknown): unknown {
  return { ...validBody(), [field]: value };
}

// The client builds save payloads and the server validates them, so what the
// reviewer can produce has to stay inside what the server will accept.
describe("what codingsRequest produces is accepted by parseBody", () => {
  it("accepts a fully coded risk", () => {
    const entry = entryWith([]);
    let draft = draftFromResponses([]);
    draft = withValue(draft, "entity", "human");
    draft = withValue(draft, "intent", "intentional");
    draft = withValue(draft, "timing", "pre-deployment");
    draft = withValue(draft, "subdomain", "1.1");
    expect(parseBody(overTheWire(entry, draft))).not.toBeNull();
  });

  it("accepts a risk marked not-a-risk from scratch", () => {
    const entry = entryWith([]);
    const draft = withNotARisk(draftFromResponses([]), true);
    expect(parseBody(overTheWire(entry, draft))).not.toBeNull();
  });

  it("accepts the switch from coded axes to not-a-risk", () => {
    const entry = entryWith(axisResponses());
    const draft = withNotARisk(draftFromResponses(entry.responses), true);
    const parsed = parseBody(overTheWire(entry, draft));
    expect(parsed?.codings.map((coding) => coding.field)).toEqual(["validity"]);
    expect(parsed?.staleReviewIds).toHaveLength(4);
  });

  it("accepts the reversal from not-a-risk back to coded axes", () => {
    const entry = entryWith([
      {
        id: "r-validity",
        field: "validity",
        value: NOT_A_RISK,
        mode: "anchored",
        comment: null,
      },
    ]);
    let draft = withNotARisk(draftFromResponses(entry.responses), false);
    draft = withValue(draft, "entity", "human");
    draft = withValue(draft, "intent", "intentional");
    draft = withValue(draft, "timing", "pre-deployment");
    draft = withValue(draft, "subdomain", "1.1");
    expect(parseBody(overTheWire(entry, draft))).not.toBeNull();
  });

  it("accepts a save that clears every coding", () => {
    const entry = entryWith(axisResponses());
    expect(
      parseBody(overTheWire(entry, draftFromResponses([]))),
    ).not.toBeNull();
  });
});

describe("parseBody", () => {
  it("accepts a well-formed body and trims the reviewer", () => {
    const parsed = parseBody(withField("reviewer", "  alice  "));
    expect(parsed?.reviewer).toBe("alice");
  });

  it("rejects a body that is not an object", () => {
    expect(parseBody(null)).toBeNull();
    expect(parseBody("alice")).toBeNull();
    expect(parseBody(undefined)).toBeNull();
  });

  it("rejects a missing or blank reviewer", () => {
    expect(parseBody(withField("reviewer", ""))).toBeNull();
    expect(parseBody(withField("reviewer", "   "))).toBeNull();
    expect(parseBody(withField("reviewer", 7))).toBeNull();
  });

  it("rejects a blank risk id", () => {
    expect(parseBody(withField("riskId", ""))).toBeNull();
  });

  it("rejects an unknown mode", () => {
    expect(parseBody(withField("mode", "sighted"))).toBeNull();
  });

  it("rejects an unknown field name", () => {
    const codings = [
      { reviewId: null, field: "vibes", value: "human", comment: null },
    ];
    expect(parseBody(withField("codings", codings))).toBeNull();
  });

  it("rejects a value outside the field's domain", () => {
    const codings = [
      { reviewId: null, field: "entity", value: "penguin", comment: null },
    ];
    expect(parseBody(withField("codings", codings))).toBeNull();
  });

  it("rejects the same field coded twice", () => {
    const codings = [
      { reviewId: null, field: "entity", value: "human", comment: null },
      { reviewId: null, field: "entity", value: "ai", comment: null },
    ];
    expect(parseBody(withField("codings", codings))).toBeNull();
  });

  it("rejects not-a-risk sitting alongside a causal axis", () => {
    const codings = [
      { reviewId: null, field: "validity", value: NOT_A_RISK, comment: null },
      { reviewId: null, field: "entity", value: "human", comment: null },
    ];
    expect(parseBody(withField("codings", codings))).toBeNull();
  });

  it("rejects a row that is both written and retired", () => {
    const body = validBody();
    body.staleReviewIds = ["r-intent"];
    expect(parseBody(body)).toBeNull();
  });

  it("rejects malformed stale review ids", () => {
    expect(parseBody(withField("staleReviewIds", ["r-old", ""]))).toBeNull();
    expect(parseBody(withField("staleReviewIds", [3]))).toBeNull();
    expect(parseBody(withField("staleReviewIds", "r-old"))).toBeNull();
  });

  it("rejects codings that are not an array", () => {
    expect(parseBody(withField("codings", {}))).toBeNull();
  });

  it("rejects a non-string comment", () => {
    const codings = [
      { reviewId: null, field: "entity", value: "human", comment: 5 },
    ];
    expect(parseBody(withField("codings", codings))).toBeNull();
  });

  it("rejects an empty review id", () => {
    const codings = [
      { reviewId: "", field: "entity", value: "human", comment: null },
    ];
    expect(parseBody(withField("codings", codings))).toBeNull();
  });
});
