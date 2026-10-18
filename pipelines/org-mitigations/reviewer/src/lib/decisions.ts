export type Disclosure = "yes" | "no" | "unsure";

export const DISCLOSURES: Disclosure[] = ["yes", "no", "unsure"];

export const DISCLOSURE_LABELS: Record<Disclosure, string> = {
  yes: "Yes",
  no: "No",
  unsure: "Unsure",
};

export interface Decision {
  disclosure: Disclosure | null;
  comment: string;
  supportingQuotes: ReadonlySet<string>;
}

export const NO_DECISION: Decision = {
  disclosure: null,
  comment: "",
  supportingQuotes: new Set(),
};

export function parseDisclosure(value: string): Disclosure {
  const disclosure = DISCLOSURES.find((candidate) => candidate === value);
  if (disclosure === undefined) {
    throw new Error(`Unknown disclosure ${value}`);
  }
  return disclosure;
}
