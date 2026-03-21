import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "document-processing",
  name: "Document Processing",
  description:
    "Shared input layer: discovers, extracts, screens, and type-classifies documents. Feeds into Actors, Risks, and Mitigations pipelines.",
  nodes: [
    // --- Input sources ---
    {
      id: "google-custom-search",
      label: "Google Custom Search",
      type: "external-service",
    },
    {
      id: "companiesmarketcap",
      label: "companiesmarketcap.com",
      type: "external-service",
    },

    // --- Processors ---
    {
      id: "greylitsearcher",
      label: "Grey literature search",
      type: "processor",
      link: {
        url: "https://github.com/MIT-FutureTech/greylitsearcher",
        label: "greylitsearcher",
      },
    },
    {
      id: "orgrev-orglist",
      label: "Company scraping",
      type: "processor",
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist",
        label: "airi-orgrev-orglist",
      },
    },
    {
      id: "fulltext-extractor",
      label: "Full-text extraction",
      type: "processor",
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgreview-fulltext",
        label: "airi-orgreview-fulltext",
      },
    },
    {
      id: "screening-orchestrator",
      label: "LLM relevance screening",
      type: "processor",
      link: {
        url: "https://github.com/MIT-FutureTech/airi-llm-screening-orchestrator",
        label: "airi-llm-screening-orchestrator",
      },
    },
    {
      id: "agentic-framework",
      label: "Agentic screening (prototype)",
      type: "proposed",
      link: {
        url: "https://github.com/MIT-FutureTech/agentic-framework",
        label: "agentic-framework",
      },
    },
    {
      id: "org-doc-classifier",
      label: "Document type classification",
      type: "processor",
      link: {
        url: "https://github.com/MIT-FutureTech/org-doc-classifier",
        label: "org-doc-classifier",
      },
    },

    // --- Pipeline-specific data stores ---
    {
      id: "airtable-grey-lit",
      label: "Airtable: Grey Literature",
      type: "datastore",
    },
    {
      id: "airtable-classified",
      label: "Airtable: classified docs",
      type: "datastore",
      link: {
        url: "https://airtable.com/appHrhJQHkZz4c82U/tblb9eEVPpV4Qqo4u",
        label: "Open in Airtable",
      },
    },
  ],
  shared: [airtableCompanies],
  edges: [
    // Input paths
    { source: "google-custom-search", target: "greylitsearcher" },
    { source: "companiesmarketcap", target: "orgrev-orglist" },

    // Scrapers → data stores
    { source: "greylitsearcher", target: "airtable-grey-lit" },
    { source: "orgrev-orglist", target: "airtable-companies" },

    // Processing chain
    { source: "airtable-grey-lit", target: "fulltext-extractor" },
    { source: "fulltext-extractor", target: "screening-orchestrator" },
    {
      source: "airtable-companies",
      target: "screening-orchestrator",
      label: "actor context",
    },
    {
      source: "screening-orchestrator",
      target: "org-doc-classifier",
      label: "approved only",
    },

    // Agentic framework (proposed replacement — same inputs as orchestrator)
    { source: "fulltext-extractor", target: "agentic-framework" },
    {
      source: "airtable-companies",
      target: "agentic-framework",
      label: "actor context",
    },

    // Output
    { source: "org-doc-classifier", target: "airtable-classified" },
  ],
};
