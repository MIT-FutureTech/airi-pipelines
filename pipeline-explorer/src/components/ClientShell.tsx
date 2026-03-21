"use client";

import dynamic from "next/dynamic";
import type { PipelineDefinition, PipelineNode } from "@/types/pipeline";

const PipelineGraph = dynamic(
  () => import("@/components/PipelineGraph").then((mod) => mod.PipelineGraph),
  { ssr: false },
);

interface ClientShellProps {
  pipelines: PipelineDefinition[];
  sharedNodes: PipelineNode[];
}

export function ClientShell({ pipelines, sharedNodes }: ClientShellProps) {
  return (
    <div className="flex flex-col h-full">
      <header className="border-b border-border px-6 py-3 shrink-0 bg-surface flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-text-primary tracking-tight">
            AIRI Pipeline Explorer
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Interactive map of the AI Risk Initiative data pipelines. Click a
            node for details.
          </p>
        </div>
      </header>
      <main className="flex-1 min-h-0">
        <PipelineGraph pipelines={pipelines} sharedNodes={sharedNodes} />
      </main>
    </div>
  );
}
