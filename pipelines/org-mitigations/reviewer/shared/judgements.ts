export type Decision = "yes" | "no" | "unsure";

export const DECISIONS: readonly Decision[] = ["yes", "no", "unsure"];

export interface Judgement {
  companyId: string;
  codeRecordId: string;
  decision: Decision | null;
  comment: string;
  supportingMitigationRecordIds: string[];
}

export interface JudgementsResponse {
  judgements: Judgement[];
}
