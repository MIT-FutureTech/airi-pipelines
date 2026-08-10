import {
  REVIEW_FIELDS,
  type ReviewField,
  type ReviewResponse,
} from "@shared/classification";

export interface ReasoningGroup {
  fields: ReviewField[];
  comment: string;
}

/**
 * Collapse repeated reasoning, keeping every distinct comment.
 *
 * The pipeline explains may use the same reasoning for multiple axes. We only
 * want to show each unique comment once.
 */
export function groupReasoning(
  responses: readonly ReviewResponse[],
): ReasoningGroup[] {
  const byField = new Map(
    responses.map((response) => [response.field, response]),
  );
  const groups: ReasoningGroup[] = [];
  const byComment = new Map<string, ReasoningGroup>();
  for (const field of REVIEW_FIELDS) {
    const comment = byField.get(field)?.comment?.trim();
    if (comment === undefined || comment === "") {
      continue;
    }
    const existing = byComment.get(comment);
    if (existing === undefined) {
      const group: ReasoningGroup = { fields: [field], comment };
      byComment.set(comment, group);
      groups.push(group);
    } else {
      existing.fields.push(field);
    }
  }
  return groups;
}
