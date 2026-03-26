"use client";

import { type ComponentType, useCallback } from "react";
import type { DetailStatus, PipelineNode } from "@/types/pipeline";
import styles from "./NodeDetailPanel.module.css";

interface NodeDetailPanelProps {
  node: PipelineNode;
  content: ComponentType | null;
  onClose: () => void;
}

const badgeConfig: Record<
  DetailStatus,
  { className: string; label: string; tooltip: string }
> = {
  verified: {
    className: styles.verifiedBadge,
    label: "\u2713 Verified",
    tooltip: "The details for this node have been verified to be accurate.",
  },
  unverified: {
    className: styles.unverifiedBadge,
    label: "? Unverified",
    tooltip:
      "The details for this node have not yet been verified and may not be entirely accurate.",
  },
  "no-details": {
    className: styles.noDetailsBadge,
    label: "No details",
    tooltip: "No details have been documented for this node yet.",
  },
};

export function NodeDetailPanel({
  node,
  content: Content,
  onClose,
}: NodeDetailPanelProps) {
  const detailStatus: DetailStatus = Content
    ? node.verified
      ? "verified"
      : "unverified"
    : "no-details";
  const badge = badgeConfig[detailStatus];
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
              <span className={badge.className} title={badge.tooltip}>
                {badge.label}
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
