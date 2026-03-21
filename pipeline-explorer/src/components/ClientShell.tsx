"use client";

import dynamic from "next/dynamic";
import type { PipelineDefinition, PipelineNode } from "@/types/pipeline";
import styles from "./ClientShell.module.css";

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
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>AIRI Pipeline Explorer</h1>
          <p className={styles.subtitle}>
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
