import type { Code, Taxonomy } from "@/lib/types";

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
