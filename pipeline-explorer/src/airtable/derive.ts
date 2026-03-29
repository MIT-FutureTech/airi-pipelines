import type {
  AccessMode,
  AirtableBase,
  AirtableTable,
  FieldAccess,
} from "@/airtable/types";

/**
 * Canonical repo ordering following the pipeline flow.
 * Repos not listed here sort alphabetically at the end.
 */
const REPO_ORDER: string[] = [
  "greylitsearcher",
  "airi-orgreview-fulltext",
  "airi-llm-screening-orchestrator",
  "agentic-framework",
  "org-doc-classifier",
  "airi-orgrev-orglist",
  "ai-actor-classifier",
  "airi-orgreview-logoprocessing",
  "airi-mitrev-classifier",
  "mitigations_review",
  "airi-navigator",
];

export function getReposForBase(base: AirtableBase): string[] {
  const repos = new Set<string>();
  for (const table of base.tables) {
    for (const field of table.fields) {
      for (const repo of Object.keys(field.access)) {
        repos.add(repo);
      }
    }
  }
  return [...repos].sort((a, b) => {
    const ia = REPO_ORDER.indexOf(a);
    const ib = REPO_ORDER.indexOf(b);
    // Both known: sort by pipeline order
    if (ia !== -1 && ib !== -1) {
      return ia - ib;
    }
    // One unknown: known repos first
    if (ia !== -1) {
      return -1;
    }
    if (ib !== -1) {
      return 1;
    }
    // Both unknown: alphabetical
    return a.localeCompare(b);
  });
}

export function hasFieldDetail(access: FieldAccess): boolean {
  return !!(access.filterFormula || access.writtenAs || access.notes);
}

export function hasTableDetail(table: AirtableTable, repo: string): boolean {
  for (const field of table.fields) {
    const access = field.access[repo];
    if (access && hasFieldDetail(access)) {
      return true;
    }
  }
  return false;
}

export function getTableAccessSummary(
  table: AirtableTable,
  repo: string,
): AccessMode | null {
  let reads = false;
  let writes = false;
  for (const field of table.fields) {
    const access = field.access[repo];
    if (!access) {
      continue;
    }
    if (access.mode === "read" || access.mode === "read-write") {
      reads = true;
    }
    if (access.mode === "write" || access.mode === "read-write") {
      writes = true;
    }
    if (reads && writes) {
      return "read-write";
    }
  }
  if (reads) {
    return "read";
  }
  if (writes) {
    return "write";
  }
  return null;
}

export function getTablePopoverContent(
  table: AirtableTable,
  repo: string,
): { reads: string[]; writes: string[]; filters: string[] } {
  const reads: string[] = [];
  const writes: string[] = [];
  const filters: string[] = [];

  for (const field of table.fields) {
    const access = field.access[repo];
    if (!access) {
      continue;
    }
    if (access.mode === "read" || access.mode === "read-write") {
      reads.push(field.name);
    }
    if (access.mode === "write" || access.mode === "read-write") {
      const label = access.writtenAs
        ? `${field.name} = ${access.writtenAs}`
        : field.name;
      writes.push(label);
    }
    if (access.filterFormula) {
      filters.push(access.filterFormula);
    }
  }

  return { reads, writes, filters };
}
