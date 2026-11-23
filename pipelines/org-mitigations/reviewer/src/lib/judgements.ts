import { DECISIONS, type Decision, type Judgement } from "@shared/judgements";

export const DECISION_LABELS: Record<Decision, string> = {
  yes: "Yes",
  no: "No",
  unsure: "Unsure",
};

export const DECISION_MARKS: Record<Decision, string> = {
  yes: "✓",
  no: "✗",
  unsure: "?",
};

export function parseDecision(value: string): Decision {
  const decision = DECISIONS.find((candidate) => candidate === value);
  if (decision === undefined) {
    throw new Error(`Unknown decision ${value}`);
  }
  return decision;
}

export function emptyJudgement(
  companyId: string,
  codeRecordId: string,
): Judgement {
  return {
    companyId,
    codeRecordId,
    decision: null,
    comment: "",
    supportingMitigationRecordIds: [],
  };
}
