import {
  AXIS_FIELDS,
  NOT_A_RISK,
  type ReviewField,
} from "./_classification.js";

export interface Coding {
  field: ReviewField;
  value: string;
}

export function isCoded(codings: readonly Coding[]): boolean {
  if (codings.some(isNotARisk)) {
    return true;
  }
  const present = new Set(codings.map((coding) => coding.field));
  return AXIS_FIELDS.every((field) => present.has(field));
}

export function isNotARisk(coding: Coding): boolean {
  return coding.field === "validity" && coding.value === NOT_A_RISK;
}
