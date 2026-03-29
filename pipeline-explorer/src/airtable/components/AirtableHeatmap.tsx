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
      <div className={styles.intro}>
        <p>
          Which repos read from and write to which Airtable tables and fields.
          Click a table row to expand its fields. Click a colored cell for
          details.
        </p>
      </div>
      <div className={styles.sections}>
        {bases.map((base) => (
          <BaseSection key={base.baseId} base={base} />
        ))}
      </div>
    </div>
  );
}
