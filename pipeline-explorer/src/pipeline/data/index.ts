import type { PipelineNode } from "@/pipeline/types";
import { pipeline as actors } from "./actors/pipeline";
import { pipeline as companyData } from "./company-data/pipeline";
import { pipeline as documentProcessing } from "./document-processing/pipeline";
import { pipeline as governance } from "./governance/pipeline";
import { pipeline as incidents } from "./incidents/pipeline";
import { pipeline as mitigations } from "./mitigations/pipeline";
import { pipeline as riskRepository } from "./risk-repository/pipeline";
import { pipeline as risks } from "./risks/pipeline";

export const allPipelines = [
  governance,
  incidents,
  riskRepository,
  documentProcessing,
  companyData,
  risks,
  actors,
  mitigations,
];

export const allSharedNodes: PipelineNode[] = (() => {
  const seen = new Map<string, PipelineNode>();
  for (const p of allPipelines) {
    for (const node of p.shared) {
      seen.set(node.id, node);
    }
  }
  return [...seen.values()];
})();
