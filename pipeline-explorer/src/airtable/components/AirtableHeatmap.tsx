"use client";

import type { AirtableBase } from "@/airtable/types";
import styles from "./AirtableHeatmap.module.css";
import { BaseSection } from "./BaseSection";

interface AirtableHeatmapProps {
  bases: AirtableBase[];
}

export function AirtableHeatmap({ bases }: AirtableHeatmapProps) {
  return (
    <div className={styles.container}>
      <div className="prose prose-sm max-w-none prose-slate">
        <p>
          Overview of which repositories read from and write to which Airtable
          tables and fields.
        </p>
        <ol>
          <li>Click a table row to expand its fields.</li>
          <li>
            Underlined cells have extra detail. Click them to see filter
            formulas, written values, and notes.
          </li>
        </ol>
      </div>
      <div className={styles.sections}>
        {bases.map((base) => (
          <BaseSection key={base.baseId} base={base} />
        ))}
      </div>
    </div>
  );
}
