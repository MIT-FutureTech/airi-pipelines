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

export interface SaveJudgementRequest {
  companyId: string;
  companyName: string;
  codeRecordId: string;
  codeKey: string;
  decision: Decision | null;
  comment: string;
  supportingMitigationRecordIds: string[];
}
