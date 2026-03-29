"use client";

import { ExternalLink } from "lucide-react";
import { useState } from "react";
import {
  getReposForBase,
  getTableAccessSummary,
  getTablePopoverContent,
  hasFieldDetail,
  hasTableDetail,
} from "@/airtable/derive";
import type { AirtableBase } from "@/airtable/types";
import { AccessCell } from "./AccessCell";
import styles from "./AccessTable.module.css";

interface AccessTableProps {
  base: AirtableBase;
}

export function AccessTable({ base }: AccessTableProps) {
  const repos = getReposForBase(base);
  const [expandedTable, setExpandedTable] = useState<string | null>(null);

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.cornerCell}>Table</th>
            {repos.map((repo) => (
              <th key={repo} className={styles.repoHeader}>
                <span className={styles.repoLabel}>{repo}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {base.tables.map((table) => {
            const isExpanded = expandedTable === table.tableId;
            return (
              <TableRows
                key={table.tableId}
                baseId={base.baseId}
                table={table}
                repos={repos}
                isExpanded={isExpanded}
                onToggle={() =>
                  setExpandedTable(isExpanded ? null : table.tableId)
                }
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function TableRows({
  baseId,
  table,
  repos,
  isExpanded,
  onToggle,
}: {
  baseId: string;
  table: AirtableBase["tables"][number];
  repos: string[];
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const airtableUrl =
    table.tableId && `https://airtable.com/${baseId}/${table.tableId}`;
  const fieldCount = table.fields.length;

  return (
    <>
      {/* Table summary row */}
      <tr
        className={`${styles.tableRow} ${isExpanded ? styles.tableRowExpanded : ""}`}
        onClick={onToggle}
      >
        <td className={styles.tableNameCell}>
          <span className={styles.chevron}>
            {isExpanded ? "\u25BC" : "\u25B6"}
          </span>
          <div className={styles.tableNameContent}>
            <div className={styles.tableNameRow}>
              <span className={styles.tableName}>{table.name}</span>
              {table.alias && (
                <span className={styles.tableAlias}>{table.alias}</span>
              )}
              {airtableUrl && (
                <a
                  href={airtableUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.externalLink}
                  title="Open in Airtable"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink size={12} />
                </a>
              )}
              <span className={styles.fieldCount}>{fieldCount} fields</span>
            </div>
            {table.description && (
              <span className={styles.tableDescription}>
                {table.description}
              </span>
            )}
          </div>
        </td>
        {repos.map((repo) => {
          const mode = getTableAccessSummary(table, repo);
          const detail = mode && hasTableDetail(table, repo);
          const popoverData =
            mode && detail ? getTablePopoverContent(table, repo) : undefined;
          return (
            <AccessCell
              key={repo}
              mode={mode}
              hasDetail={!!detail}
              popover={
                popoverData
                  ? {
                      repo,
                      reads: popoverData.reads,
                      writes: popoverData.writes,
                      filters: popoverData.filters,
                    }
                  : undefined
              }
            />
          );
        })}
      </tr>

      {/* Expanded field rows */}
      {isExpanded &&
        table.fields.map((field) => {
          const hasAnyAccess = repos.some((r) => field.access[r]);
          return (
            <tr
              key={field.name}
              className={`${styles.fieldRow} ${!hasAnyAccess ? styles.fieldRowMuted : ""}`}
            >
              <td className={styles.fieldNameCell}>
                <span className={styles.fieldName}>{field.name}</span>
                <span className={styles.fieldType}>{field.type}</span>
              </td>
              {repos.map((repo) => {
                const access = field.access[repo];
                const detail = access ? hasFieldDetail(access) : false;
                return (
                  <AccessCell
                    key={repo}
                    mode={access?.mode ?? null}
                    hasDetail={detail}
                    popover={
                      access && detail
                        ? { repo, fieldName: field.name, access }
                        : undefined
                    }
                  />
                );
              })}
            </tr>
          );
        })}
    </>
  );
}
