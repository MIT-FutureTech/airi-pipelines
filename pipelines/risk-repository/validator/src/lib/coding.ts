import type { ReviewResponse } from "@api/_classification";
import { AXIS_FIELDS } from "@/lib/fields";

export function isNotARisk(responses: ReviewResponse[]): boolean {
  return responses.some(
    (response) =>
      response.field === "validity" && response.value === "not-a-risk",
  );
}

export function isRiskCoded(responses: ReviewResponse[]): boolean {
  if (isNotARisk(responses)) {
    return true;
  }
  const present = new Set(responses.map((response) => response.field));
  return AXIS_FIELDS.every((field) => present.has(field));
}
