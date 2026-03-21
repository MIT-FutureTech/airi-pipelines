"use client";

import { useSelectNode } from "./NodeSelectionContext";

interface NodeLinkProps {
  id: string;
  children: React.ReactNode;
}

export function NodeLink({ id, children }: NodeLinkProps) {
  const selectNode = useSelectNode();

  return (
    <a
      href={`?node=${id}`}
      onClick={(e) => {
        e.preventDefault();
        selectNode(id);
      }}
      className="text-blue-600 dark:text-blue-400 underline cursor-pointer hover:text-blue-800 dark:hover:text-blue-300"
    >
      {children}
    </a>
  );
}
