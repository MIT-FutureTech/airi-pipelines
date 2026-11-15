import type {
  Company,
  CompanyDocument,
  Domain,
  LocatedEvidence,
} from "@/lib/types";

export interface CellSelection {
  company: Company;
  domain: Domain;
  evidence: LocatedEvidence[];
}

export function quoteKey(item: LocatedEvidence): string {
  return `${item.excerpt_id} ${item.mitigation_name} ${item.quote}`;
}

export function cellKey(companyId: string, domainCode: string): string {
  return `${companyId} ${domainCode}`;
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
    const key = cellKey(companyId, item.domain_code);
    const cell = cells.get(key);
    if (cell === undefined) {
      cells.set(key, [item]);
    } else {
      cell.push(item);
    }
  }
  return cells;
}
