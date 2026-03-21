"use client";

import { Handle, type NodeProps, Position } from "@xyflow/react";
import type { NodeType } from "@/types/pipeline";

interface PipelineNodeData {
  label: string;
  nodeType: NodeType;
  link?: { url: string; label: string };
  [key: string]: unknown;
}

const stylesByType: Record<
  NodeType,
  { card: string; badge: string; badgeLabel: string }
> = {
  processor: {
    card: "border-blue-200 bg-white ring-1 ring-blue-100",
    badge: "bg-blue-50 text-blue-700",
    badgeLabel: "Processor",
  },
  datastore: {
    card: "border-amber-200 bg-white ring-1 ring-amber-100 rounded-xl",
    badge: "bg-amber-50 text-amber-700",
    badgeLabel: "Data Store",
  },
  "external-service": {
    card: "border-slate-200 bg-white ring-1 ring-slate-100 border-dashed",
    badge: "bg-slate-50 text-slate-600",
    badgeLabel: "External",
  },
  "manual-step": {
    card: "border-slate-200 bg-slate-50/50 ring-1 ring-slate-100 border-dashed",
    badge: "bg-slate-100 text-slate-500",
    badgeLabel: "Manual",
  },
  proposed: {
    card: "border-dashed border-slate-200 bg-slate-50/30 ring-1 ring-slate-50 opacity-60",
    badge: "bg-slate-50 text-slate-400",
    badgeLabel: "Proposed",
  },
};

export function PipelineNodeComponent({ data }: NodeProps) {
  const nodeData = data as PipelineNodeData;
  const style = stylesByType[nodeData.nodeType] ?? stylesByType.processor;

  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-slate-300 !w-2 !h-2 !border-white !border-2"
      />
      <div
        className={`border-2 px-4 py-3 rounded-lg shadow-sm min-w-[160px] text-center cursor-pointer hover:shadow-md hover:-translate-y-px transition-all duration-150 ${style.card}`}
      >
        <div className="mb-1.5">
          <span
            className={`inline-block text-[10px] font-medium uppercase tracking-wider px-1.5 py-0.5 rounded ${style.badge}`}
          >
            {style.badgeLabel}
          </span>
        </div>
        <div className="text-sm font-medium text-text-primary leading-snug">
          {nodeData.label}
        </div>
        {nodeData.link && (
          <a
            href={nodeData.link.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-[11px] text-accent hover:text-accent-hover underline underline-offset-2 decoration-accent/30 hover:decoration-accent mt-1.5 inline-block transition-colors"
          >
            {nodeData.link.label} ↗
          </a>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-slate-300 !w-2 !h-2 !border-white !border-2"
      />
    </>
  );
}
