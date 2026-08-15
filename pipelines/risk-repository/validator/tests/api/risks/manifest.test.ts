import type { AirtableRecord } from "@api/_airtable";
import { buildEntry } from "@api/risks/manifest";
import type {
  ReviewFields,
  ReviewMode,
  RiskFields,
} from "@shared/classification";
import { describe, expect, it } from "vitest";

const RISK_ID = "recRisk";

const PIPELINE_COMMENT = "PIPELINE-ONLY-REASONING";
const PIPELINE_SUBDOMAIN = "7.6";

function risk(fields: RiskFields): AirtableRecord<RiskFields> {
  return {
    id: RISK_ID,
    createdTime: "2026-01-01T00:00:00.000Z",
    fields: {
      ReadableId: "Lee2025.01",
      Name: "Example risk",
      Origin: "model-added, human-approved",
      ...fields,
    },
  };
}

function review(
  id: string,
  reviewer: string,
  fields: ReviewFields,
): AirtableRecord<ReviewFields> {
  return {
    id,
    createdTime: "2026-01-01T00:00:00.000Z",
    fields: {
      Risk: [RISK_ID],
      Reviewer: reviewer,
      Mode: "anchored",
      ...fields,
    },
  };
}

// Rows for the reviewer, the pipeline, and a second human, all on one risk.
function crowdedRisk(): Map<string, AirtableRecord<ReviewFields>[]> {
  return new Map([
    [
      RISK_ID,
      [
        review("own1", "alice", { Field: "entity", Value: "human" }),
        review("own2", "alice", { Field: "subdomain", Value: "1.1" }),
        review("pipe1", "pipeline:v1", {
          Field: "entity",
          Value: "ai",
          Comment: PIPELINE_COMMENT,
        }),
        review("pipe2", "pipeline:v1", {
          Field: "subdomain",
          Value: PIPELINE_SUBDOMAIN,
        }),
        review("other1", "bob", { Field: "entity", Value: "other" }),
      ],
    ],
  ]);
}

function entryFor(mode: ReviewMode) {
  return buildEntry(risk({}), new Set([RISK_ID]), crowdedRisk(), "alice", mode);
}

describe("buildEntry in blind mode", () => {
  it("withholds the pipeline's codings", () => {
    expect(entryFor("blind").pipelineResponses).toEqual([]);
  });

  it("leaves no trace of the pipeline anywhere in the entry", () => {
    const serialised = JSON.stringify(entryFor("blind"));
    expect(serialised).not.toContain(PIPELINE_COMMENT);
    expect(serialised).not.toContain(PIPELINE_SUBDOMAIN);
    expect(serialised).not.toContain("pipeline:");
  });

  it("still returns the reviewer's own codings", () => {
    expect(entryFor("blind").responses.map((r) => r.id)).toEqual([
      "own1",
      "own2",
    ]);
  });
});

describe("buildEntry in anchored mode", () => {
  it("returns the pipeline's codings", () => {
    expect(entryFor("anchored").pipelineResponses.map((r) => r.id)).toEqual([
      "pipe1",
      "pipe2",
    ]);
  });

  it("returns the reviewer's own codings alongside them", () => {
    expect(entryFor("anchored").responses.map((r) => r.id)).toEqual([
      "own1",
      "own2",
    ]);
  });
});

describe("buildEntry reviewer isolation", () => {
  it("never returns another human's codings, in either mode", () => {
    for (const mode of ["blind", "anchored"] as const) {
      const entry = entryFor(mode);
      const ids = [...entry.responses, ...entry.pipelineResponses].map(
        (r) => r.id,
      );
      expect(ids).not.toContain("other1");
    }
  });

  it("refuses a review row that names no reviewer", () => {
    const anonymous: AirtableRecord<ReviewFields> = {
      id: "recAnon",
      createdTime: "2026-01-01T00:00:00.000Z",
      fields: {
        Risk: [RISK_ID],
        Field: "entity",
        Value: "human",
        Mode: "anchored",
      },
    };
    expect(() =>
      buildEntry(
        risk({}),
        new Set([RISK_ID]),
        new Map([[RISK_ID, [anonymous]]]),
        "alice",
        "anchored",
      ),
    ).toThrow("recAnon");
  });

  it("returns nothing when the risk has no reviews at all", () => {
    const entry = buildEntry(
      risk({}),
      new Set([RISK_ID]),
      new Map(),
      "alice",
      "anchored",
    );
    expect(entry.responses).toEqual([]);
    expect(entry.pipelineResponses).toEqual([]);
  });
});

describe("buildEntry risk fields", () => {
  it("carries the risk across", () => {
    const entry = buildEntry(
      risk({
        Parent: ["recParent"],
        Description: "A description",
        DescriptionPage: 4,
        SupportingQuote: "A quote",
        AdditionalEvidence: '[{"quote":"more"}]',
      }),
      new Set([RISK_ID]),
      new Map(),
      "alice",
      "anchored",
    );
    expect(entry.id).toBe(RISK_ID);
    expect(entry.readableId).toBe("Lee2025.01");
    expect(entry.name).toBe("Example risk");
    expect(entry.parentId).toBe("recParent");
    expect(entry.origin).toBe("model-added, human-approved");
    expect(entry.description).toBe("A description");
    expect(entry.descriptionPage).toBe(4);
    expect(entry.supportingQuote).toBe("A quote");
    expect(entry.additionalEvidence).toEqual([
      { index: 0, fields: [{ key: "quote", value: "more" }] },
    ]);
  });

  it("fills in the optional fields when Airtable leaves them empty", () => {
    const entry = buildEntry(
      risk({}),
      new Set(),
      new Map(),
      "alice",
      "anchored",
    );
    expect(entry.parentId).toBeNull();
    expect(entry.description).toBe("");
    expect(entry.descriptionPage).toBeNull();
    expect(entry.supportingQuote).toBe("");
    expect(entry.additionalEvidence).toEqual([]);
  });

  it("takes codability from the set it is given", () => {
    const codable = buildEntry(
      risk({}),
      new Set([RISK_ID]),
      new Map(),
      "alice",
      "anchored",
    );
    const notCodable = buildEntry(
      risk({}),
      new Set(),
      new Map(),
      "alice",
      "anchored",
    );
    expect(codable.codable).toBe(true);
    expect(notCodable.codable).toBe(false);
  });

  it("refuses a risk that is missing an identity or an origin", () => {
    for (const missing of ["ReadableId", "Name", "Origin"] as const) {
      const fields = risk({}).fields;
      delete fields[missing];
      const incomplete: AirtableRecord<RiskFields> = {
        id: RISK_ID,
        createdTime: "2026-01-01T00:00:00.000Z",
        fields,
      };
      expect(() =>
        buildEntry(incomplete, new Set(), new Map(), "alice", "anchored"),
      ).toThrow(RISK_ID);
    }
  });
});
