import type { PipelineNode } from "@/pipeline/types";

/**
 * Shared nodes used by multiple pipelines.
 * These are displayed outside any pipeline group box.
 */

export const airtableCompanies: PipelineNode = {
  id: "airtable-companies",
  label: "Airtable: Companies",
  type: "datastore",
  verified: false,
};

export const pdfKeywordExtraction: PipelineNode = {
  id: "pdf-keyword-extraction",
  label: "PDF keyword extraction",
  type: "processor",
  verified: false,
  link: {
    url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist/tree/main/pdf_analysis",
    label: "airi-orgrev-orglist/pdf_analysis",
  },
};
