import type { RiskEntry } from "@shared/classification";

export type RiskIndex = Map<string, RiskEntry>;

export function indexRisks(risks: RiskEntry[]): RiskIndex {
  return new Map(risks.map((risk) => [risk.id, risk]));
}

export function ancestorsOf(index: RiskIndex, entry: RiskEntry): RiskEntry[] {
  const chain: RiskEntry[] = [];
  let parentId = entry.parentId;
  while (parentId !== null && chain.length < index.size) {
    const parent = index.get(parentId);
    if (parent === undefined) {
      break;
    }
    chain.unshift(parent);
    parentId = parent.parentId;
  }
  return chain;
}

export function depthOf(index: RiskIndex, entry: RiskEntry): number {
  return ancestorsOf(index, entry).length;
}
