import type { PipelineDefinition } from "@/pipeline/types";
import { airtableClassifiedDocs } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "document-processing",
  name: "Document Processing",
  description:
    "Discovers, extracts, screens, and type-classifies corporate documents. Feeds into Risks and Mitigations pipelines.",
  nodes: [
    {
      id: "google-custom-search",
      label: "Google Custom Search",
      type: "external-service",
      verified: false,
    },
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
    {
      id: "airtable-grey-lit",
      label: "Airtable: Grey Literature",
      type: "datastore",
      verified: false,
      link: {
        url: "https://airtable.com/appHrhJQHkZz4c82U/tblb9eEVPpV4Qqo4u",
        label: "Open in Airtable",
      },
    },
    airtableClassifiedDocs,
  ],
  shared: [],
  edges: [
    { source: "google-custom-search", target: "grey-lit-search" },
    { source: "grey-lit-search", target: "airtable-grey-lit" },
    { source: "airtable-grey-lit", target: "fulltext-extraction" },
    { source: "fulltext-extraction", target: "relevance-screening" },
    {
      source: "relevance-screening",
      target: "doc-type-classification",
      label: "approved only",
    },
    // Agentic framework (proposed replacement — same inputs as orchestrator)
    { source: "fulltext-extraction", target: "agentic-screening" },
    { source: "doc-type-classification", target: "airtable-classified" },
  ],
};
