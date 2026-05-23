import type { Decision, Stage } from "@api/_shared";

export const STAGE: Stage = "abstract";

export interface DocumentFields {
  QuickRef?: string;
  DocTitle?: string;
  Abstract?: string;
}

export interface DecisionFields {
  Document?: string[];
  Reviewer?: string;
  Stage?: Stage;
  Decision?: Decision;
  Comments?: string;
}
