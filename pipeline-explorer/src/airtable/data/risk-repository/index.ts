import type { AirtableBase } from "@/airtable/types";
import { abstractScreening } from "./abstract-screening";
import { aiRiskDatabase } from "./ai-risk-database";
import { fullTextScreening } from "./full-text-screening";

export const riskRepository: AirtableBase = {
  baseId: "app32FOUBa5WcUfEO",
  name: "AI Risk Repository",
  tables: [abstractScreening, fullTextScreening, aiRiskDatabase],
};
