import type { ReviewResponse, RiskEntry } from "@api/_classification";
import { AXIS_FIELDS, NOT_A_RISK } from "@/lib/fields";

export function isNotARisk(responses: ReviewResponse[]): boolean {
  return responses.some(
    (response) =>
      response.field === "validity" && response.value === NOT_A_RISK,
  );
}

export function isRiskCoded(responses: ReviewResponse[]): boolean {
  if (isNotARisk(responses)) {
    return true;
  }
  const present = new Set(responses.map((response) => response.field));
  return AXIS_FIELDS.every((field) => present.has(field));
}

export function codableRisks(risks: RiskEntry[]): RiskEntry[] {
  return risks.filter((risk) => risk.codable);
}

export function pipelineIsReady(risks: RiskEntry[]): boolean {
  return codableRisks(risks).every((risk) =>
    isRiskCoded(risk.pipelineResponses),
  );
}
