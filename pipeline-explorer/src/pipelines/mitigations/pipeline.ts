import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies, corporatePdfAnalysis } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "mitigations",
  name: "Mitigations",
  description:
    "Classifies AI risk mitigation actions into a 3-level, 44-code hierarchical taxonomy. Two input paths: corporate documents and research papers.",
  nodes: [
    // --- Corporate docs path ---
    {
      id: "mitigations-corp-classifier",
      label: "LLM mitigation classification (corporate)",
      type: "processor",
    },
    {
      id: "mitigations-corp-output",
      label: "Mitigation classifications (CSV)",
      type: "datastore",
    },

    // --- Research papers path ---
    {
      id: "academic-sources",
      label: "ArXiv, CrossRef, SSRN, Scopus",
      type: "external-service",
    },
    {
      id: "mitigations-review",
      label: "mitigations_review",
      type: "processor",
    },
    {
      id: "airtable-mitigations",
      label: "Airtable: Mitigations V2",
      type: "datastore",
    },
    {
      id: "mitigations-classifier",
      label: "airi-mitrev-classifier",
      type: "processor",
    },
    {
      id: "airtable-mitigations-classified",
      label: "Airtable: Mitigations (classified)",
      type: "datastore",
    },
  ],
  shared: [airtableCompanies, corporatePdfAnalysis],
  edges: [
    // Corporate docs path
    {
      source: "airtable-companies",
      target: "corporate-pdf-analysis",
      label: "corporate PDFs",
    },
    {
      source: "corporate-pdf-analysis",
      target: "mitigations-corp-classifier",
      label: "keyword mentions",
    },
    {
      source: "mitigations-corp-classifier",
      target: "mitigations-corp-output",
    },

    // Research papers path
    { source: "academic-sources", target: "mitigations-review" },
    {
      source: "mitigations-review",
      target: "airtable-mitigations",
      label: "screened papers",
    },
    { source: "airtable-mitigations", target: "mitigations-classifier" },
    {
      source: "mitigations-classifier",
      target: "airtable-mitigations-classified",
    },
  ],
};
