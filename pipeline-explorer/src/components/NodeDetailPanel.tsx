"use client";

import { type ComponentType, useCallback } from "react";
import styles from "./NodeDetailPanel.module.css";

interface NodeDetailPanelProps {
  nodeId: string;
  nodeLabel: string;
  nodeType: string;
  verified: boolean;
  content: ComponentType | null;
  onClose: () => void;
}

export function NodeDetailPanel({
  nodeLabel,
  nodeType,
  verified,
  content: Content,
  onClose,
}: NodeDetailPanelProps) {
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
            <h2 className={styles.title}>{nodeLabel}</h2>
            <div className={styles.meta}>
              <span className={styles.type}>{nodeType}</span>
              <span
                className={
                  verified ? styles.verifiedBadge : styles.unverifiedBadge
                }
              >
                {verified ? "\u2713 Verified" : "? Unverified"}
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
