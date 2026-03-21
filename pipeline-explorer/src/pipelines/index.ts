import type { PipelineNode } from "@/types/pipeline";
import { pipeline as documentProcessing } from "./document-processing/pipeline";
import { pipeline as actors } from "./actors/pipeline";

export const allPipelines = [documentProcessing, actors];

export const allSharedNodes: PipelineNode[] = (() => {
  const seen = new Map<string, PipelineNode>();
  for (const p of allPipelines) {
    for (const node of p.shared) {
      seen.set(node.id, node);
    }
  }
  return [...seen.values()];
})();
