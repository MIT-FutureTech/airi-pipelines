import type { PipelineDefinition } from "@/pipeline/types";
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
      verified: false,
    },
    {
      id: "companiesmarketcap",
      label: "companiesmarketcap.com",
      type: "external-service",
      verified: false,
    },

    // --- Processors ---
    {
      id: "grey-lit-search",
      label: "Grey literature search",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/greylitsearcher",
        label: "greylitsearcher",
      },
    },
    {
      id: "company-scraping",
      label: "Company scraping",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist",
        label: "airi-orgrev-orglist",
      },
    },
    {
      id: "fulltext-extraction",
      label: "Full-text extraction",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgreview-fulltext",
        label: "airi-orgreview-fulltext",
      },
    },
    {
      id: "relevance-screening",
      label: "LLM relevance screening",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-llm-screening-orchestrator",
        label: "airi-llm-screening-orchestrator",
      },
    },
    {
      id: "agentic-screening",
      label: "Agentic screening (prototype)",
      type: "proposed",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/agentic-framework",
        label: "agentic-framework",
      },
    },
    {
      id: "doc-type-classification",
      label: "Document type classification",
      type: "processor",
      verified: false,
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
      verified: false,
    },
    {
      id: "airtable-classified",
      label: "Airtable: classified docs",
      type: "datastore",
      verified: false,
      link: {
        url: "https://airtable.com/appHrhJQHkZz4c82U/tblb9eEVPpV4Qqo4u",
        label: "Open in Airtable",
      },
    },
  ],
  shared: [airtableCompanies],
  edges: [
    // Input paths
    { source: "google-custom-search", target: "grey-lit-search" },
    { source: "companiesmarketcap", target: "company-scraping" },

    // Scrapers → data stores
    { source: "grey-lit-search", target: "airtable-grey-lit" },
    { source: "company-scraping", target: "airtable-companies" },

    // Processing chain
    { source: "airtable-grey-lit", target: "fulltext-extraction" },
    { source: "fulltext-extraction", target: "relevance-screening" },
    {
      source: "relevance-screening",
      target: "doc-type-classification",
      label: "approved only",
    },

    // Agentic framework (proposed replacement — same inputs as orchestrator)
    { source: "fulltext-extraction", target: "agentic-screening" },

    // Output
    { source: "doc-type-classification", target: "airtable-classified" },
  ],
};
