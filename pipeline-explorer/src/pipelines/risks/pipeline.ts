import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies, pdfKeywordExtraction } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "risks",
  name: "Risks",
  description:
    "Classifies AI risk mentions from corporate documents into a 24-code taxonomy across 7 risk domains.",
  nodes: [
    {
      id: "risk-classification",
      label: "LLM risk classification",
      type: "processor",
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist/tree/main/llm_classification",
        label: "airi-orgrev-orglist/llm_classification",
      },
    },
    {
      id: "risks-output",
      label: "Risk classifications (CSV)",
      type: "datastore",
    },
  ],
  shared: [airtableCompanies, pdfKeywordExtraction],
  edges: [
    {
      source: "airtable-companies",
      target: "pdf-keyword-extraction",
      label: "corporate PDFs",
    },
    {
      source: "pdf-keyword-extraction",
      target: "risk-classification",
      label: "keyword mentions",
    },
    { source: "risk-classification", target: "risks-output" },
  ],
};
