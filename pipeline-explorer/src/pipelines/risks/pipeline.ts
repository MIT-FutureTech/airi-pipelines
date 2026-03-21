import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "risks",
  name: "Risks",
  description:
    "Classifies AI risk mentions from corporate documents into a 24-code taxonomy across 7 risk domains.",
  nodes: [
    {
      id: "risks-pdf-analysis",
      label: "PDF keyword extraction",
      type: "processor",
    },
    {
      id: "risks-classifier",
      label: "LLM risk classification",
      type: "processor",
    },
    {
      id: "risks-output",
      label: "Risk classifications (CSV)",
      type: "datastore",
    },
  ],
  shared: [airtableCompanies],
  edges: [
    {
      source: "airtable-companies",
      target: "risks-pdf-analysis",
      label: "corporate PDFs",
    },
    {
      source: "risks-pdf-analysis",
      target: "risks-classifier",
      label: "keyword mentions",
    },
    { source: "risks-classifier", target: "risks-output" },
  ],
};
