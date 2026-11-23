import type { Code, Company, Mitigation, Quote, Taxonomy } from "@/lib/types";

export interface CellSelection {
  company: Company;
  code: Code;
  mitigations: Mitigation[];
}

export function cellKey(companyId: string, codeRecordId: string): string {
  return `${companyId} ${codeRecordId}`;
}

export function mitigationsByCell(
  mitigations: Mitigation[],
  taxonomy: Taxonomy,
): Map<string, Mitigation[]> {
  const cells = new Map<string, Mitigation[]>();
  for (const mitigation of mitigations) {
    for (const codeRecordId of codeRecordIds(mitigation, taxonomy)) {
      const key = cellKey(mitigation.company_id, codeRecordId);
      const cell = cells.get(key);
      if (cell === undefined) {
        cells.set(key, [mitigation]);
      } else {
        cell.push(mitigation);
      }
    }
  }
  return cells;
}

export function quotesByMitigation(quotes: Quote[]): Map<string, Quote[]> {
  return Map.groupBy(quotes, (quote) => quote.mitigation_record_id);
}

export function cellQuotes(
  mitigations: Mitigation[],
  quotes: Map<string, Quote[]>,
): Quote[] {
  return mitigations.flatMap((mitigation) => {
    const mitigationQuotes = quotes.get(mitigation.record_id);
    if (mitigationQuotes === undefined) {
      throw new Error(`Mitigation ${mitigation.mitigation_id} has no quotes`);
    }
    return mitigationQuotes;
  });
}

function codeRecordIds(mitigation: Mitigation, taxonomy: Taxonomy): string[] {
  switch (taxonomy) {
    case "Domain":
      return [mitigation.domain_record_id];
    case "Instrument":
      return [mitigation.instrument_record_id];
    case "Practice":
      return mitigation.practice_record_ids;
  }
}
