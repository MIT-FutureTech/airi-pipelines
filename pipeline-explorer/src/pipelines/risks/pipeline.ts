import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies, corporatePdfAnalysis } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "risks",
  name: "Risks",
  description:
    "Classifies AI risk mentions from corporate documents into a 24-code taxonomy across 7 risk domains.",
  nodes: [
    {
      id: "risks-classifier",
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
  shared: [airtableCompanies, corporatePdfAnalysis],
  edges: [
    {
      source: "airtable-companies",
      target: "corporate-pdf-analysis",
      label: "corporate PDFs",
    },
    {
      source: "corporate-pdf-analysis",
      target: "risks-classifier",
      label: "keyword mentions",
    },
    { source: "risks-classifier", target: "risks-output" },
  ],
};
