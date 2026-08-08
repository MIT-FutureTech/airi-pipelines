import { AXIS_FIELDS, NOT_A_RISK, type ReviewField } from "./classification.js";

export interface Coding {
  field: ReviewField;
  value: string;
}

function isNotARiskCoding(coding: Coding): boolean {
  return coding.field === "validity" && coding.value === NOT_A_RISK;
}

export function isNotARisk(codings: readonly Coding[]): boolean {
  return codings.some(isNotARiskCoding);
}

export function isCoded(codings: readonly Coding[]): boolean {
  if (isNotARisk(codings)) {
    return true;
  }
  const present = new Set(codings.map((coding) => coding.field));
  return AXIS_FIELDS.every((field) => present.has(field));
}
