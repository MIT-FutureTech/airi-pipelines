"use client";

import { Handle, type NodeProps, Position } from "@xyflow/react";
import type { DetailStatus, NodeType, PipelineNode } from "@/types/pipeline";
import styles from "./PipelineNode.module.css";

type PipelineNodeData = PipelineNode & { detailStatus: DetailStatus };

const variantsByType: Record<
  NodeType,
  { card: string; badge: string; badgeLabel: string }
> = {
  processor: {
    card: styles.processor,
    badge: styles.badgeProcessor,
    badgeLabel: "Processor",
  },
  datastore: {
    card: styles.datastore,
    badge: styles.badgeDatastore,
    badgeLabel: "Data Store",
  },
  "external-service": {
    card: styles.externalService,
    badge: styles.badgeExternal,
    badgeLabel: "External",
  },
  "manual-step": {
    card: styles.manualStep,
    badge: styles.badgeManual,
    badgeLabel: "Manual",
  },
  proposed: {
    card: styles.proposed,
    badge: styles.badgeProposed,
    badgeLabel: "Proposed",
  },
};

const detailStatusIcons: Record<DetailStatus, string> = {
  verified: "\u2713",
  unverified: "?",
  "no-details": "",
};

const detailStatusTooltips: Record<DetailStatus, string> = {
  verified: "The details for this node have been verified to be accurate.",
  unverified:
    "The details for this node have not yet been verified and may not be entirely accurate.",
  "no-details": "No details have been documented for this node yet.",
};

export function PipelineNodeComponent({ data }: NodeProps) {
  const nodeData = data as unknown as PipelineNodeData;
  const variant = variantsByType[nodeData.type] ?? variantsByType.processor;

  return (
    <>
      <Handle type="target" position={Position.Top} />
      <div className={`${styles.card} ${variant.card}`}>
        <span
          className={styles[`detailStatus-${nodeData.detailStatus}`]}
          title={detailStatusTooltips[nodeData.detailStatus]}
        >
          {detailStatusIcons[nodeData.detailStatus]}
        </span>
        <div className="mb-1.5">
          <span className={`${styles.badge} ${variant.badge}`}>
            {variant.badgeLabel}
          </span>
        </div>
        <div className={styles.label}>{nodeData.label}</div>
        {nodeData.link && (
          <a
            href={nodeData.link.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className={styles.link}
          >
            {nodeData.link.label} ↗
          </a>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} />
    </>
  );
}
