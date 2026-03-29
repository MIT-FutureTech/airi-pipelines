"use client";

import { useState } from "react";
import type { AirtableBase } from "@/airtable/types";
import { AccessTable } from "./AccessTable";
import styles from "./BaseSection.module.css";

interface BaseSectionProps {
  base: AirtableBase;
  defaultExpanded?: boolean;
}

export function BaseSection({
  base,
  defaultExpanded = true,
}: BaseSectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const tableCount = base.tables.length;

  return (
    <section className={styles.section}>
      <button
        type="button"
        className={styles.header}
        onClick={() => setExpanded(!expanded)}
      >
        <span className={styles.chevron}>{expanded ? "\u25BC" : "\u25B6"}</span>
        <h2 className={styles.name}>{base.name}</h2>
        <code className={styles.baseId}>{base.baseId}</code>
        <span className={styles.count}>
          {tableCount} {tableCount === 1 ? "table" : "tables"}
        </span>
      </button>
      {expanded && <AccessTable base={base} />}
    </section>
  );
}
