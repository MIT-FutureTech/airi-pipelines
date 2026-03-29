import type { AirtableBase } from "@/airtable/types";
import { llmPrompts } from "./llm-prompts";
import { sysRevMitigationDatabase } from "./mitigation-database";
import { sysRevDocuments } from "./sysrev-documents";

export const mitigationDatabase: AirtableBase = {
  baseId: "appUJl8KRAUMeIVXs",
  name: "AI Risk Mitigation Database",
  tables: [sysRevMitigationDatabase, llmPrompts, sysRevDocuments],
};
