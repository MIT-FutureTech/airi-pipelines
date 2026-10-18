import type {
  Code,
  Company,
  CompanyDocument,
  LocatedEvidence,
} from "@/lib/types";

export interface CellSelection {
  company: Company;
  code: Code;
  evidence: LocatedEvidence[];
}

export function quoteKey(item: LocatedEvidence): string {
  return `${item.excerpt_id} ${item.mitigation} ${item.quote}`;
}

export function cellKey(companyId: string, code: string): string {
  return `${companyId} ${code}`;
}

export function evidenceByCell(
  evidence: LocatedEvidence[],
  documents: CompanyDocument[],
): Map<string, LocatedEvidence[]> {
  const companyIds = new Map(
    documents.map((document) => [document.document_id, document.company_id]),
  );
  const cells = new Map<string, LocatedEvidence[]>();
  for (const item of evidence) {
    const companyId = companyIds.get(item.document_id);
    if (companyId === undefined) {
      throw new Error(
        `Evidence refers to unknown document ${item.document_id}`,
      );
    }
    const key = cellKey(companyId, item.code);
    const cell = cells.get(key);
    if (cell === undefined) {
      cells.set(key, [item]);
    } else {
      cell.push(item);
    }
  }
  return cells;
}
