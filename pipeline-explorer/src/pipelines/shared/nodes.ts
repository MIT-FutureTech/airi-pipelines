import type { PipelineNode } from "@/types/pipeline";

/**
 * Shared nodes used by multiple pipelines.
 * These are displayed outside any pipeline group box.
 */

export const airtableCompanies: PipelineNode = {
  id: "airtable-companies",
  label: "Airtable: Companies",
  type: "datastore",
};
