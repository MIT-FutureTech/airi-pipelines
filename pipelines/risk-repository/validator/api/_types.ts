import type { Decision } from "@api/_shared";

export const STAGE = "abstract_screening";

export interface DocumentFields {
  QuickRef?: string;
  DocTitle?: string;
  Abstract?: string;
}

export interface ValidationFields {
  Document?: string[];
  Reviewer?: string;
  Stage?: string;
  Decision?: Decision;
  Comments?: string;
}
