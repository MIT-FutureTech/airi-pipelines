import {
  type CodingWrite,
  NOT_A_RISK,
  REVIEW_FIELDS,
  type ReviewField,
  type ReviewMode,
  type ReviewResponse,
  type RiskEntry,
  type SaveCodingsRequest,
} from "@shared/classification";
import type { Coding } from "@shared/coding";

/** One reviewer's in-progress verdict on one risk, before it is saved. */
export type Draft = Record<ReviewField, string | null>;

export function draftFromResponses(
  responses: readonly ReviewResponse[],
): Draft {
  const draft: Draft = {
    validity: null,
    entity: null,
    intent: null,
    timing: null,
    subdomain: null,
  };
  for (const response of responses) {
    draft[response.field] = response.value;
  }
  return draft;
}

export function draftEquals(a: Draft, b: Draft): boolean {
  return REVIEW_FIELDS.every((field) => a[field] === b[field]);
}

export function draftCodings(draft: Draft): Coding[] {
  const codings: Coding[] = [];
  for (const field of REVIEW_FIELDS) {
    const value = draft[field];
    if (value !== null) {
      codings.push({ field, value });
    }
  }
  return codings;
}

export function withNotARisk(draft: Draft, notARisk: boolean): Draft {
  if (!notARisk) {
    return { ...draft, validity: null };
  }
  return {
    validity: NOT_A_RISK,
    entity: null,
    intent: null,
    timing: null,
    subdomain: null,
  };
}

interface RequestParams {
  reviewer: string;
  mode: ReviewMode;
  entry: RiskEntry;
  draft: Draft;
}

export function codingsRequest({
  reviewer,
  mode,
  entry,
  draft,
}: RequestParams): SaveCodingsRequest {
  const persisted = new Map(
    entry.responses.map((response) => [response.field, response]),
  );
  const codings: CodingWrite[] = [];
  for (const field of REVIEW_FIELDS) {
    const value = draft[field];
    if (value !== null) {
      codings.push({
        reviewId: persisted.get(field)?.id ?? null,
        field,
        value,
        comment: null,
      });
    }
  }
  const kept = new Set(codings.map((coding) => coding.reviewId));
  return {
    reviewer,
    riskId: entry.id,
    mode,
    codings,
    staleReviewIds: entry.responses
      .filter((response) => !kept.has(response.id))
      .map((response) => response.id),
  };
}
