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

export const corporatePdfAnalysis: PipelineNode = {
  id: "corporate-pdf-analysis",
  label: "PDF keyword extraction",
  type: "processor",
  link: {
    url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist/tree/main/pdf_analysis",
    label: "airi-orgrev-orglist/pdf_analysis",
  },
};
