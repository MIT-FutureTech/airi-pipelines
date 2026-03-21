"use client";

import type { NodeProps } from "@xyflow/react";

export function PipelineGroupNode({ data }: NodeProps) {
  return (
    <div className="w-full h-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30">
      <div className="px-3 py-2 text-sm font-semibold text-gray-500 dark:text-gray-400">
        {(data as { label: string }).label}
      </div>
    </div>
  );
}
