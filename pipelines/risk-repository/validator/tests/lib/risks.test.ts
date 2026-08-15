import {
  NOT_A_RISK,
  type ReviewField,
  type ReviewResponse,
  type RiskEntry,
} from "@shared/classification";
import { describe, expect, it } from "vitest";
import { codableRisks, pipelineIsReady } from "@/lib/risks";

function response(field: ReviewField, value: string): ReviewResponse {
  return { id: `rec-${field}`, field, value, mode: "anchored", comment: null };
}

const FULLY_CODED: ReviewResponse[] = [
  response("entity", "human"),
  response("intent", "intentional"),
  response("timing", "pre-deployment"),
  response("subdomain", "1.1"),
];

function entry(
  id: string,
  codable: boolean,
  pipelineResponses: ReviewResponse[],
): RiskEntry {
  return {
    id,
    readableId: `Lee2025.${id}`,
    name: `Risk ${id}`,
    parentId: null,
    codable,
    origin: "human-added",
    description: "",
    descriptionPage: null,
    supportingQuote: "",
    additionalEvidence: [],
    responses: [],
    pipelineResponses,
  };
}

describe("codableRisks", () => {
  it("keeps only the risks worth coding", () => {
    const risks = [
      entry("r1", true, []),
      entry("r2", false, []),
      entry("r3", true, []),
    ];
    expect(codableRisks(risks).map((risk) => risk.id)).toEqual(["r1", "r3"]);
  });

  it("is empty when nothing is codable", () => {
    expect(codableRisks([entry("r1", false, [])])).toEqual([]);
  });
});

describe("pipelineIsReady", () => {
  it("is ready once every codable risk is coded", () => {
    const risks = [
      entry("r1", true, FULLY_CODED),
      entry("r2", true, [response("validity", NOT_A_RISK)]),
    ];
    expect(pipelineIsReady(risks)).toBe(true);
  });

  it("is not ready while a codable risk is unfinished", () => {
    const risks = [
      entry("r1", true, FULLY_CODED),
      entry("r2", true, [response("entity", "human")]),
    ];
    expect(pipelineIsReady(risks)).toBe(false);
  });

  it("ignores risks that are not codable", () => {
    const risks = [entry("r1", true, FULLY_CODED), entry("r2", false, [])];
    expect(pipelineIsReady(risks)).toBe(true);
  });

  it("is ready when there is nothing to code", () => {
    expect(pipelineIsReady([])).toBe(true);
    expect(pipelineIsReady([entry("r1", false, [])])).toBe(true);
  });

  it("reads the pipeline's codings, not the reviewer's", () => {
    const risk = entry("r1", true, []);
    risk.responses = FULLY_CODED;
    expect(pipelineIsReady([risk])).toBe(false);
  });
});
