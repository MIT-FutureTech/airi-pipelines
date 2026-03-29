"use client";

import type { AccessMode, FieldAccess } from "@/airtable/types";
import styles from "./AccessCell.module.css";
import { CellPopover } from "./CellPopover";

const modeLabels: Record<AccessMode, string> = {
  read: "R",
  write: "W",
  "read-write": "R/W",
};

const modeStyles: Record<AccessMode, string> = {
  read: styles.read,
  write: styles.write,
  "read-write": styles.readWrite,
};

interface AccessCellProps {
  mode: AccessMode | null;
  /** If provided, the cell is clickable and shows a popover. */
  popover?: {
    repo: string;
    fieldName?: string;
    access?: FieldAccess;
    /** For table-level cells: aggregated info */
    reads?: string[];
    writes?: string[];
    filters?: string[];
  };
}

function PopoverContent({
  popover,
}: {
  popover: NonNullable<AccessCellProps["popover"]>;
}) {
  const { repo, fieldName, access, reads, writes, filters } = popover;

  return (
    <div className={styles.popoverBody}>
      <div className={styles.popoverHeader}>
        <strong>{repo}</strong>
        {fieldName && <span className={styles.popoverField}>{fieldName}</span>}
      </div>

      {/* Field-level detail */}
      {access?.filterFormula && (
        <div className={styles.popoverSection}>
          <span className={styles.popoverLabel}>Filter</span>
          <code className={styles.popoverCode}>{access.filterFormula}</code>
        </div>
      )}
      {access?.writtenAs && (
        <div className={styles.popoverSection}>
          <span className={styles.popoverLabel}>Writes</span>
          <span>{access.writtenAs}</span>
        </div>
      )}
      {access?.notes && (
        <div className={styles.popoverSection}>
          <span className={styles.popoverLabel}>Note</span>
          <span>{access.notes}</span>
        </div>
      )}

      {/* Table-level aggregated detail */}
      {reads && reads.length > 0 && (
        <div className={styles.popoverSection}>
          <span className={styles.popoverLabel}>
            Reads ({reads.length} fields)
          </span>
          <span className={styles.popoverList}>{reads.join(", ")}</span>
        </div>
      )}
      {writes && writes.length > 0 && (
        <div className={styles.popoverSection}>
          <span className={styles.popoverLabel}>
            Writes ({writes.length} fields)
          </span>
          <span className={styles.popoverList}>{writes.join(", ")}</span>
        </div>
      )}
      {filters && filters.length > 0 && (
        <div className={styles.popoverSection}>
          <span className={styles.popoverLabel}>Filters</span>
          {filters.map((f) => (
            <code key={f} className={styles.popoverCode}>
              {f}
            </code>
          ))}
        </div>
      )}
    </div>
  );
}

export function AccessCell({ mode, popover }: AccessCellProps) {
  if (!mode) {
    return <td className={styles.cell} />;
  }

  const badge = (
    <button type="button" className={`${styles.badge} ${modeStyles[mode]}`}>
      {modeLabels[mode]}
    </button>
  );

  if (popover) {
    return (
      <td className={styles.cell}>
        <CellPopover content={<PopoverContent popover={popover} />}>
          {badge}
        </CellPopover>
      </td>
    );
  }

  return <td className={styles.cell}>{badge}</td>;
}
