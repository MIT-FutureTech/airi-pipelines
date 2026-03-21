"use client";

import { type ComponentType, useCallback } from "react";

interface NodeDetailPanelProps {
  nodeId: string;
  nodeLabel: string;
  nodeType: string;
  content: ComponentType | null;
  onClose: () => void;
}

export function NodeDetailPanel({
  nodeLabel,
  nodeType,
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
      {/* Backdrop */}
      <button
        type="button"
        className="fixed inset-0 z-40 appearance-none bg-black/5 backdrop-blur-[2px] border-none cursor-default animate-fade-in"
        onClick={onClose}
        aria-label="Close panel"
      />

      {/* Panel */}
      <div
        role="dialog"
        ref={(el) => el?.focus()}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="fixed top-0 right-0 h-full w-[480px] max-w-full z-50 bg-surface-elevated border-l border-border shadow-2xl overflow-y-auto outline-none animate-slide-in-right"
      >
        <div className="sticky top-0 bg-surface-elevated/95 backdrop-blur-sm border-b border-border px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-base font-semibold text-text-primary tracking-tight">
              {nodeLabel}
            </h2>
            <span className="text-xs text-text-muted font-medium">
              {nodeType}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-text-muted hover:text-text-primary w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-secondary transition-colors text-lg leading-none"
          >
            &times;
          </button>
        </div>

        <div className="px-6 py-6 prose prose-sm max-w-none prose-slate">
          {Content ? (
            <Content />
          ) : (
            <p className="text-text-muted italic">
              No additional details available for this node.
            </p>
          )}
        </div>
      </div>
    </>
  );
}
