"use client";

import dynamic from "next/dynamic";
import type { PipelineDefinition, PipelineNode } from "@/pipeline/types";

const PipelineGraph = dynamic(
  () =>
    import("@/pipeline/components/PipelineGraph").then(
      (mod) => mod.PipelineGraph,
    ),
  { ssr: false },
);

interface PipelineViewProps {
  pipelines: PipelineDefinition[];
  sharedNodes: PipelineNode[];
}

export function PipelineView({ pipelines, sharedNodes }: PipelineViewProps) {
  return <PipelineGraph pipelines={pipelines} sharedNodes={sharedNodes} />;
}
