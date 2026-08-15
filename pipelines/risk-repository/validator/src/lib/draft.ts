import {
  AXIS_FIELDS,
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

export interface FieldDraft {
  value: string | null;
  comment: string;
}

/** One reviewer's in-progress verdict on one risk, before it is saved. */
export type Draft = Record<ReviewField, FieldDraft>;

function emptyField(): FieldDraft {
  return { value: null, comment: "" };
}

export function draftFromResponses(
  responses: readonly ReviewResponse[],
): Draft {
  const draft: Draft = {
    validity: emptyField(),
    entity: emptyField(),
    intent: emptyField(),
    timing: emptyField(),
    subdomain: emptyField(),
  };
  for (const response of responses) {
    draft[response.field] = {
      value: response.value,
      comment: response.comment ?? "",
    };
  }
  return draft;
}

export function draftEquals(a: Draft, b: Draft): boolean {
  return REVIEW_FIELDS.every(
    (field) =>
      a[field].value === b[field].value &&
      a[field].comment === b[field].comment,
  );
}

export function draftCodings(draft: Draft): Coding[] {
  const codings: Coding[] = [];
  for (const field of REVIEW_FIELDS) {
    const { value } = draft[field];
    if (value !== null) {
      codings.push({ field, value });
    }
  }
  return codings;
}

export function withValue(
  draft: Draft,
  field: ReviewField,
  value: string,
): Draft {
  return { ...draft, [field]: { ...draft[field], value } };
}

export function withComment(
  draft: Draft,
  field: ReviewField,
  comment: string,
): Draft {
  return { ...draft, [field]: { ...draft[field], comment } };
}

export function withNotARisk(draft: Draft, notARisk: boolean): Draft {
  if (!notARisk) {
    return { ...draft, validity: emptyField() };
  }
  const next: Draft = {
    ...draft,
    validity: { value: NOT_A_RISK, comment: draft.validity.comment },
  };
  for (const field of AXIS_FIELDS) {
    next[field] = emptyField();
  }
  return next;
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
    const { value, comment } = draft[field];
    if (value !== null) {
      const trimmed = comment.trim();
      codings.push({
        reviewId: persisted.get(field)?.id ?? null,
        field,
        value,
        comment: trimmed === "" ? null : trimmed,
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
