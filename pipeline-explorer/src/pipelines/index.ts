import type { PipelineNode } from "@/types/pipeline";
import { pipeline as actors } from "./actors/pipeline";
import { pipeline as documentProcessing } from "./document-processing/pipeline";
import { pipeline as governance } from "./governance/pipeline";
import { pipeline as incidents } from "./incidents/pipeline";
import { pipeline as mitigations } from "./mitigations/pipeline";
import { pipeline as risks } from "./risks/pipeline";

export const allPipelines = [
  documentProcessing,
  actors,
  risks,
  mitigations,
  governance,
  incidents,
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
