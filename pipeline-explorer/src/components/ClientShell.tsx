"use client";

import dynamic from "next/dynamic";
import type { PipelineDefinition } from "@/types/pipeline";

const PipelineGraph = dynamic(
  () =>
    import("@/components/PipelineGraph").then((mod) => mod.PipelineGraph),
  { ssr: false },
);

interface ClientShellProps {
  pipelines: PipelineDefinition[];
}

export function ClientShell({ pipelines }: ClientShellProps) {
  return (
    <div className="flex flex-col h-full">
      <header className="border-b border-gray-200 dark:border-gray-700 px-6 py-4 shrink-0">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          AIRI Pipeline Explorer
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Interactive map of the AI Risk Initiative data pipelines. Click a node
          for details.
        </p>
      </header>
      <main className="flex-1 min-h-0">
        <PipelineGraph pipelines={pipelines} />
      </main>
    </div>
  );
}
