"use client";

import { useCallback, type ComponentType } from "react";

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
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Panel */}
      <div
        ref={(el) => el?.focus()}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="fixed top-0 right-0 h-full w-[480px] max-w-full z-50 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 shadow-xl overflow-y-auto outline-none"
      >
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {nodeLabel}
            </h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {nodeType}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none"
          >
            &times;
          </button>
        </div>

        <div className="px-6 py-6 prose prose-sm dark:prose-invert max-w-none">
          {Content ? (
            <Content />
          ) : (
            <p className="text-gray-500 dark:text-gray-400 italic">
              No additional details available for this node.
            </p>
          )}
        </div>
      </div>
    </>
  );
}
