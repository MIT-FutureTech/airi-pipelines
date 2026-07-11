import type { AirtableBase } from "@/airtable/types";
import { governanceMapping } from "./governance-mapping";
import { incidentTracker } from "./incident-tracker";
import { mitigationDatabase } from "./mitigation-database";
import { organisationalReview } from "./organisational-review";
import { riskRepository } from "./risk-repository";

export const airtableBases: AirtableBase[] = [
  organisationalReview,
  mitigationDatabase,
  governanceMapping,
  incidentTracker,
  riskRepository,
];
