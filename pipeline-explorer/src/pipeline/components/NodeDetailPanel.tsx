"use client";

import { type ComponentType, useCallback } from "react";
import {
  type DetailStatus,
  detailStatusConfig,
  type PipelineNode,
} from "@/pipeline/types";
import styles from "./NodeDetailPanel.module.css";

interface NodeDetailPanelProps {
  node: PipelineNode;
  detailStatus: DetailStatus;
  content: ComponentType | null;
  onClose: () => void;
}

const badgeStyles: Record<DetailStatus, string> = {
  verified: styles.verifiedBadge,
  unverified: styles.unverifiedBadge,
  "no-details": styles.noDetailsBadge,
};

export function NodeDetailPanel({
  node,
  detailStatus,
  content: Content,
  onClose,
}: NodeDetailPanelProps) {
  const status = detailStatusConfig[detailStatus];
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  return (
    <>
      <button
        type="button"
        className={styles.backdrop}
        onClick={onClose}
        aria-label="Close panel"
      />

      <div
        role="dialog"
        ref={(el) => el?.focus()}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className={styles.panel}
      >
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>{node.label}</h2>
            <div className={styles.meta}>
              <span className={styles.type}>{node.type}</span>
              <span
                className={badgeStyles[detailStatus]}
                title={status.tooltip}
              >
                {status.label}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className={styles.closeButton}
          >
            &times;
          </button>
        </div>

        <div className="px-6 py-6 prose prose-sm max-w-none prose-slate">
          {Content ? (
            <Content />
          ) : (
            <p className={styles.emptyState}>
              No additional details available for this node.
            </p>
          )}
        </div>
      </div>
    </>
  );
}
