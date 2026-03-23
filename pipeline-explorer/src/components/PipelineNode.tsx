"use client";

import { Handle, type NodeProps, Position } from "@xyflow/react";
import type { NodeType } from "@/types/pipeline";
import styles from "./PipelineNode.module.css";

interface PipelineNodeData {
  label: string;
  nodeType: NodeType;
  verified: boolean;
  link?: { url: string; label: string };
  [key: string]: unknown;
}

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
  const nodeData = data as PipelineNodeData;
  const variant = variantsByType[nodeData.nodeType] ?? variantsByType.processor;

  return (
    <>
      <Handle type="target" position={Position.Top} />
      <div className={`${styles.card} ${variant.card}`}>
        <div className="mb-1.5 flex items-center justify-center gap-1.5">
          <span className={`${styles.badge} ${variant.badge}`}>
            {variant.badgeLabel}
          </span>
          <span
            className={
              nodeData.verified ? styles.verifiedIcon : styles.unverifiedIcon
            }
            title={nodeData.verified ? "Verified" : "Unverified"}
          >
            {nodeData.verified ? "\u2713" : "?"}
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
