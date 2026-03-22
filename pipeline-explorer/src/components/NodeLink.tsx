"use client";

import styles from "./NodeLink.module.css";
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
      className={styles.link}
    >
      {children}
    </a>
  );
}
