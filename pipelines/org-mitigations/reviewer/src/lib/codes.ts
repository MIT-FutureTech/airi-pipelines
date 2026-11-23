import type { Code, Taxonomy } from "@/lib/types";

export const TAXONOMIES: Taxonomy[] = ["Domain", "Instrument", "Practice"];

export const TAXONOMY_LABELS: Record<Taxonomy, string> = {
  Domain: "Domains",
  Instrument: "Instruments",
  Practice: "Practices",
};

export function parseTaxonomy(value: string): Taxonomy {
  const taxonomy = TAXONOMIES.find((candidate) => candidate === value);
  if (taxonomy === undefined) {
    throw new Error(`Unknown taxonomy ${value}`);
  }
  return taxonomy;
}

export interface CodeGroup {
  name: string | null;
  codes: Code[];
}

export function codeGroups(codes: Code[], taxonomy: Taxonomy): CodeGroup[] {
  const ordered = codes
    .filter((code) => code.taxonomy === taxonomy)
    .toSorted((a, b) => a.order - b.order);
  const groups: CodeGroup[] = [];
  for (const code of ordered) {
    const last = groups.at(-1);
    if (last !== undefined && last.name === code.group) {
      last.codes.push(code);
    } else {
      groups.push({ name: code.group, codes: [code] });
    }
  }
  return groups;
}

export function shortLabel(code: Code): string {
  return code.code === null
    ? code.name
    : `${code.code} ${code.short_name ?? code.name}`;
}

export function fullLabel(code: Code): string {
  return code.code === null ? code.name : `${code.code} ${code.name}`;
}
