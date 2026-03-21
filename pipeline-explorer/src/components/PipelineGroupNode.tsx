"use client";

import type { NodeProps } from "@xyflow/react";

export function PipelineGroupNode({ data }: NodeProps) {
  return (
    <div className="w-full h-full rounded-xl border-2 border-border bg-surface-secondary/60">
      <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
        {(data as { label: string }).label}
      </div>
    </div>
  );
}
