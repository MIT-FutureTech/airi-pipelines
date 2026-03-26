"use client";

import { Handle, type NodeProps, Position } from "@xyflow/react";
import {
  type DetailStatus,
  detailStatusConfig,
  type NodeType,
  type PipelineNode,
} from "@/types/pipeline";
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

export function PipelineNodeComponent({ data }: NodeProps) {
  const nodeData = data as unknown as PipelineNodeData;
  const variant = variantsByType[nodeData.type] ?? variantsByType.processor;
  const status = detailStatusConfig[nodeData.detailStatus];

  return (
    <>
      <Handle type="target" position={Position.Top} />
      <div className={`${styles.card} ${variant.card}`}>
        <span
          className={styles[`detailStatus-${nodeData.detailStatus}`]}
          title={status.tooltip}
        >
          {status.icon}
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
