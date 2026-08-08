import type { RiskEntry } from "@shared/classification";
import { isCoded } from "@shared/coding";

export function codableRisks(risks: RiskEntry[]): RiskEntry[] {
  return risks.filter((risk) => risk.codable);
}

export function pipelineIsReady(risks: RiskEntry[]): boolean {
  return codableRisks(risks).every((risk) => isCoded(risk.pipelineResponses));
}
