import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies, pdfKeywordExtraction } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "mitigations",
  name: "Mitigations",
  description:
    "Classifies AI risk mitigation actions into a 3-level, 44-code hierarchical taxonomy. Two input paths: corporate documents and research papers.",
  nodes: [
    // --- Corporate docs path ---
    {
      id: "mitigation-classification-corporate",
      label: "LLM mitigation classification (corporate)",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist/tree/main/llm_classification",
        label: "airi-orgrev-orglist/llm_classification",
      },
    },
    {
      id: "mitigations-corp-output",
      label: "Mitigation classifications (CSV)",
      type: "datastore",
      verified: false,
    },

    // --- Research papers path ---
    {
      id: "academic-sources",
      label: "ArXiv, CrossRef, SSRN, Scopus",
      type: "external-service",
      verified: false,
    },
    {
      id: "systematic-lit-review",
      label: "Systematic literature review",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/mitigations_review",
        label: "mitigations_review",
      },
    },
    {
      id: "airtable-mitigations",
      label: "Airtable: Mitigations V2",
      type: "datastore",
      verified: false,
    },
    {
      id: "mitigation-taxonomy-classification",
      label: "Mitigation taxonomy classifier",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-mitrev-classifier",
        label: "airi-mitrev-classifier",
      },
    },
    {
      id: "airtable-mitigations-classified",
      label: "Airtable: Mitigations (classified)",
      type: "datastore",
      verified: false,
    },
  ],
  shared: [airtableCompanies, pdfKeywordExtraction],
  edges: [
    // Corporate docs path
    {
      source: "airtable-companies",
      target: "pdf-keyword-extraction",
      label: "corporate PDFs",
    },
    {
      source: "pdf-keyword-extraction",
      target: "mitigation-classification-corporate",
      label: "keyword mentions",
    },
    {
      source: "mitigation-classification-corporate",
      target: "mitigations-corp-output",
    },

    // Research papers path
    { source: "academic-sources", target: "systematic-lit-review" },
    {
      source: "systematic-lit-review",
      target: "airtable-mitigations",
      label: "screened papers",
    },
    {
      source: "airtable-mitigations",
      target: "mitigation-taxonomy-classification",
    },
    {
      source: "mitigation-taxonomy-classification",
      target: "airtable-mitigations-classified",
    },
  ],
};
