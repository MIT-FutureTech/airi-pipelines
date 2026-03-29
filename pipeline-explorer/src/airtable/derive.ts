import type { AccessMode, AirtableBase, AirtableTable } from "@/airtable/types";

export function getReposForBase(base: AirtableBase): string[] {
  const repos = new Set<string>();
  for (const table of base.tables) {
    for (const field of table.fields) {
      for (const repo of Object.keys(field.access)) {
        repos.add(repo);
      }
    }
  }
  return [...repos].sort();
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
