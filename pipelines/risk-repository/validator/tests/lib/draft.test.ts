import {
  NOT_A_RISK,
  type ReviewField,
  type ReviewResponse,
  type RiskEntry,
} from "@shared/classification";
import { conflictsWithNotARisk } from "@shared/coding";
import { describe, expect, it } from "vitest";
import {
  codingsRequest,
  type Draft,
  draftCodings,
  draftEquals,
  draftFromResponses,
  withComment,
  withNotARisk,
  withValue,
} from "@/lib/draft";

function response(
  id: string,
  field: ReviewField,
  value: string,
  comment: string | null,
): ReviewResponse {
  return { id, field, value, mode: "anchored", comment };
}

function axisResponses(): ReviewResponse[] {
  return [
    response("r-entity", "entity", "human", null),
    response("r-intent", "intent", "intentional", null),
    response("r-timing", "timing", "pre-deployment", null),
    response("r-subdomain", "subdomain", "1.1", null),
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

function request(entry: RiskEntry, draft: Draft) {
  return codingsRequest({ reviewer: "alice", mode: "anchored", entry, draft });
}

describe("draftFromResponses", () => {
  it("leaves every field empty when there are no responses", () => {
    const draft = draftFromResponses([]);
    expect(draft).toEqual({
      validity: { value: null, comment: "" },
      entity: { value: null, comment: "" },
      intent: { value: null, comment: "" },
      timing: { value: null, comment: "" },
      subdomain: { value: null, comment: "" },
    });
  });

  it("carries the value and comment of each response", () => {
    const draft = draftFromResponses([
      response("r1", "entity", "ai", "because of X"),
    ]);
    expect(draft.entity).toEqual({ value: "ai", comment: "because of X" });
  });

  it("renders a null comment as an empty string", () => {
    const draft = draftFromResponses([response("r1", "entity", "ai", null)]);
    expect(draft.entity.comment).toBe("");
  });

  it("lets the last response for a field win", () => {
    const draft = draftFromResponses([
      response("r1", "entity", "ai", null),
      response("r2", "entity", "human", null),
    ]);
    expect(draft.entity.value).toBe("human");
  });
});

describe("draftEquals", () => {
  it("is true for drafts built from the same responses", () => {
    expect(
      draftEquals(
        draftFromResponses(axisResponses()),
        draftFromResponses(axisResponses()),
      ),
    ).toBe(true);
  });

  it("is false when any value differs", () => {
    const base = draftFromResponses(axisResponses());
    expect(draftEquals(base, withValue(base, "entity", "ai"))).toBe(false);
  });

  it("is false when any comment differs", () => {
    const base = draftFromResponses(axisResponses());
    expect(draftEquals(base, withComment(base, "entity", "edited"))).toBe(
      false,
    );
  });
});

describe("draftCodings", () => {
  it("omits fields that have no value", () => {
    const draft = draftFromResponses([response("r1", "entity", "ai", null)]);
    expect(draftCodings(draft)).toEqual([{ field: "entity", value: "ai" }]);
  });

  it("is empty for an untouched draft", () => {
    expect(draftCodings(draftFromResponses([]))).toEqual([]);
  });
});

describe("withValue", () => {
  it("does not mutate the draft it is given", () => {
    const before = draftFromResponses([]);
    withValue(before, "entity", "ai");
    expect(before.entity.value).toBeNull();
  });

  it("leaves the comment and the other fields alone", () => {
    const base = withComment(draftFromResponses([]), "entity", "note");
    const next = withValue(base, "entity", "ai");
    expect(next.entity).toEqual({ value: "ai", comment: "note" });
    expect(next.intent).toEqual({ value: null, comment: "" });
  });
});

describe("withNotARisk", () => {
  it("clears the causal axes when turned on", () => {
    const draft = withNotARisk(draftFromResponses(axisResponses()), true);
    expect(draft.validity.value).toBe(NOT_A_RISK);
    expect(draft.entity.value).toBeNull();
    expect(draft.intent.value).toBeNull();
    expect(draft.timing.value).toBeNull();
    expect(draft.subdomain.value).toBeNull();
  });

  it("keeps the validity comment when turned on", () => {
    const base = withComment(
      draftFromResponses([]),
      "validity",
      "not in scope",
    );
    expect(withNotARisk(base, true).validity.comment).toBe("not in scope");
  });

  it("clears only validity when turned off", () => {
    const draft = withNotARisk(draftFromResponses(axisResponses()), false);
    expect(draft.validity).toEqual({ value: null, comment: "" });
    expect(draft.entity.value).toBe("human");
  });

  it("leaves no draft that the shared rule would call a conflict", () => {
    const draft = withNotARisk(draftFromResponses(axisResponses()), true);
    expect(conflictsWithNotARisk(draftCodings(draft))).toBe(false);
  });
});

describe("codingsRequest", () => {
  it("passes the reviewer, risk, and mode through", () => {
    const entry = entryWith([]);
    const saved = request(entry, draftFromResponses([]));
    expect(saved.reviewer).toBe("alice");
    expect(saved.riskId).toBe("rec-risk");
    expect(saved.mode).toBe("anchored");
  });

  it("sends a null review id for a coding that was never saved", () => {
    const entry = entryWith([]);
    const draft = withValue(draftFromResponses([]), "entity", "ai");
    expect(request(entry, draft).codings).toEqual([
      { reviewId: null, field: "entity", value: "ai", comment: null },
    ]);
  });

  it("reuses the existing review id when a coding is edited", () => {
    const entry = entryWith(axisResponses());
    const draft = withValue(
      draftFromResponses(entry.responses),
      "entity",
      "ai",
    );
    const saved = request(entry, draft);
    expect(saved.codings).toContainEqual({
      reviewId: "r-entity",
      field: "entity",
      value: "ai",
      comment: null,
    });
    expect(saved.staleReviewIds).toEqual([]);
  });

  it("orders codings by field rather than by draft or response order", () => {
    const entry = entryWith([
      response("r-subdomain", "subdomain", "1.1", null),
      response("r-entity", "entity", "human", null),
    ]);
    const saved = request(entry, draftFromResponses(entry.responses));
    expect(saved.codings.map((coding) => coding.field)).toEqual([
      "entity",
      "subdomain",
    ]);
  });

  it("retires the review row for a field that was cleared", () => {
    const entry = entryWith(axisResponses());
    const draft: Draft = {
      ...draftFromResponses(entry.responses),
      subdomain: { value: null, comment: "" },
    };
    const saved = request(entry, draft);
    expect(saved.codings.map((coding) => coding.field)).toEqual([
      "entity",
      "intent",
      "timing",
    ]);
    expect(saved.staleReviewIds).toEqual(["r-subdomain"]);
  });

  it("retires all four axis rows when the risk becomes not-a-risk", () => {
    const entry = entryWith(axisResponses());
    const draft = withNotARisk(draftFromResponses(entry.responses), true);
    const saved = request(entry, draft);
    expect(saved.codings).toEqual([
      { reviewId: null, field: "validity", value: NOT_A_RISK, comment: null },
    ]);
    expect(saved.staleReviewIds.toSorted()).toEqual([
      "r-entity",
      "r-intent",
      "r-subdomain",
      "r-timing",
    ]);
  });

  it("retires the validity row when a not-a-risk verdict is reversed", () => {
    const entry = entryWith([
      response("r-validity", "validity", NOT_A_RISK, null),
    ]);
    let draft = withNotARisk(draftFromResponses(entry.responses), false);
    draft = withValue(draft, "entity", "human");
    draft = withValue(draft, "intent", "intentional");
    draft = withValue(draft, "timing", "pre-deployment");
    draft = withValue(draft, "subdomain", "1.1");
    const saved = request(entry, draft);
    expect(saved.staleReviewIds).toEqual(["r-validity"]);
    expect(saved.codings.every((coding) => coding.reviewId === null)).toBe(
      true,
    );
  });

  it("trims comments and drops ones that are only whitespace", () => {
    const entry = entryWith([]);
    let draft = withValue(draftFromResponses([]), "entity", "ai");
    draft = withComment(draft, "entity", "  spaced out  ");
    draft = withValue(draft, "intent", "intentional");
    draft = withComment(draft, "intent", "   ");
    const saved = request(entry, draft);
    expect(saved.codings[0].comment).toBe("spaced out");
    expect(saved.codings[1].comment).toBeNull();
  });

  it("never retires a row it is also writing to", () => {
    const entry = entryWith(axisResponses());
    const drafts: Draft[] = [
      draftFromResponses(entry.responses),
      withNotARisk(draftFromResponses(entry.responses), true),
      withValue(draftFromResponses(entry.responses), "entity", "ai"),
      {
        ...draftFromResponses(entry.responses),
        timing: { value: null, comment: "" },
      },
    ];
    for (const draft of drafts) {
      const saved = request(entry, draft);
      const written = new Set(saved.codings.map((coding) => coding.reviewId));
      expect(saved.staleReviewIds.some((id) => written.has(id))).toBe(false);
    }
  });
});
