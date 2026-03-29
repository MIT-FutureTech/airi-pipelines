"use client";

import type { NodeProps } from "@xyflow/react";
import styles from "./PipelineGroupNode.module.css";

export function PipelineGroupNode({ data }: NodeProps) {
  return (
    <div className={styles.group}>
      <div className={styles.label}>{(data as { label: string }).label}</div>
    </div>
  );
}
