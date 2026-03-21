import type { PipelineDefinition } from "@/types/pipeline";

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
      position: { x: 0, y: 0 },
    },
    {
      id: "companiesmarketcap",
      label: "companiesmarketcap.com",
      type: "external-service",
      position: { x: 450, y: 0 },
    },

    // --- Scrapers ---
    {
      id: "greylitsearcher",
      label: "greylitsearcher",
      type: "repo",
      position: { x: 0, y: 150 },
    },
    {
      id: "orgrev-orglist",
      label: "airi-orgrev-orglist",
      type: "repo",
      position: { x: 450, y: 150 },
    },

    // --- Data stores ---
    {
      id: "airtable-grey-lit",
      label: "Airtable: Grey Literature",
      type: "datastore",
      position: { x: 0, y: 350 },
    },
    {
      id: "airtable-companies",
      label: "Airtable: Companies",
      type: "datastore",
      position: { x: 450, y: 350 },
    },

    // --- Processing ---
    {
      id: "fulltext-extractor",
      label: "airi-orgreview-fulltext",
      type: "repo",
      position: { x: 0, y: 550 },
    },
    {
      id: "screening-orchestrator",
      label: "airi-llm-screening-orchestrator",
      type: "repo",
      position: { x: 0, y: 750 },
    },
    {
      id: "agentic-framework",
      label: "agentic-framework",
      type: "proposed",
      position: { x: 350, y: 750 },
    },
    {
      id: "org-doc-classifier",
      label: "org-doc-classifier",
      type: "repo",
      position: { x: 0, y: 950 },
    },

    // --- Output ---
    {
      id: "airtable-classified",
      label: "Airtable: classified docs",
      type: "datastore",
      position: { x: 0, y: 1150 },
      url: "https://airtable.com/appHrhJQHkZz4c82U/tblb9eEVPpV4Qqo4u",
    },
  ],
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
