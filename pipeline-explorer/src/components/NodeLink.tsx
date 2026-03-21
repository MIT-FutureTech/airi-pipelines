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
      className="text-accent underline underline-offset-2 decoration-accent/30 cursor-pointer hover:text-accent-hover hover:decoration-accent-hover transition-colors"
    >
      {children}
    </a>
  );
}
