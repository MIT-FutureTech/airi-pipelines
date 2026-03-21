"use client";

import { Handle, type NodeProps, Position } from "@xyflow/react";
import type { NodeType } from "@/types/pipeline";

interface PipelineNodeData {
  label: string;
  nodeType: NodeType;
  link?: { url: string; label: string };
  [key: string]: unknown;
}

const stylesByType: Record<NodeType, string> = {
  processor: "border-blue-500 bg-blue-50 dark:bg-blue-950",
  datastore: "border-amber-500 bg-amber-50 dark:bg-amber-950 rounded-xl",
  "external-service":
    "border-gray-400 bg-gray-50 dark:bg-gray-900 border-dashed",
  "manual-step":
    "border-gray-400 bg-gray-50 dark:bg-gray-900 border-dotted opacity-75",
  proposed: "border-gray-300 bg-gray-50 dark:bg-gray-900 opacity-50",
};

const labelsByType: Record<NodeType, string> = {
  processor: "Processor",
  datastore: "Data Store",
  "external-service": "External",
  "manual-step": "Manual",
  proposed: "Proposed",
};

export function PipelineNodeComponent({ data }: NodeProps) {
  const nodeData = data as PipelineNodeData;
  const typeStyle = stylesByType[nodeData.nodeType] ?? stylesByType.processor;
  const typeLabel = labelsByType[nodeData.nodeType];

  return (
    <>
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <div
        className={`border-2 px-4 py-3 rounded-lg shadow-sm min-w-[160px] text-center cursor-pointer hover:shadow-md transition-shadow ${typeStyle}`}
      >
        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
          {typeLabel}
        </div>
        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {nodeData.label}
        </div>
        {nodeData.link && (
          <a
            href={nodeData.link.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 underline mt-1 inline-block"
          >
            {nodeData.link.label} ↗
          </a>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-gray-400"
      />
    </>
  );
}
