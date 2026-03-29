import type { PipelineNode } from "@/pipeline/types";

/**
 * Shared nodes used by multiple pipelines.
 * These are displayed outside any pipeline group box.
 */

export const governanceVisualizations: PipelineNode = {
  id: "governance-visualizations",
  label: "Gov & incident visualizations",
  type: "processor",
  verified: false,
  link: {
    url: "https://github.com/MIT-FutureTech/governance-visualizations",
    label: "governance-visualizations",
  },
};

export const airtableCompanies: PipelineNode = {
  id: "airtable-companies",
  label: "Airtable: Companies",
  type: "datastore",
  verified: false,
  link: {
    url: "https://airtable.com/appHrhJQHkZz4c82U/tblurwszwgrluMLrB",
    label: "Open in Airtable",
  },
};

export const airtableClassifiedDocs: PipelineNode = {
  id: "airtable-classified",
  label: "Airtable: classified docs",
  type: "datastore",
  verified: false,
  link: {
    url: "https://airtable.com/appHrhJQHkZz4c82U/tblb9eEVPpV4Qqo4u",
    label: "Open in Airtable",
  },
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
