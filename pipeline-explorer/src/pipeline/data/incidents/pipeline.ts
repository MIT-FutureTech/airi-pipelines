import type { PipelineDefinition } from "@/pipeline/types";

export const pipeline: PipelineDefinition = {
  id: "incidents",
  name: "Incidents",
  description:
    "Classifies AI incidents from AIID into subdomains, causal factors, severity, and purpose. Uses LLM classification. Pipeline repos live in a separate GitHub org.",
  nodes: [
    {
      id: "ai-incident-database",
      label: "AI Incident Database",
      type: "external-service",
      verified: false,
      link: {
        url: "https://incidentdatabase.ai/",
        label: "incidentdatabase.ai",
      },
    },
    {
      id: "incident-ingestion",
      label: "Incident ingestion",
      type: "processor",
      verified: false,
    },
    {
      id: "incident-classification",
      label: "LLM Incident classification",
      type: "processor",
      verified: false,
    },
    {
      id: "airtable-incidents",
      label: "Airtable: Incident Tracker",
      type: "datastore",
      verified: false,
    },
  ],
  shared: [],
  edges: [
    { source: "ai-incident-database", target: "incident-ingestion" },
    { source: "incident-ingestion", target: "incident-classification" },
    { source: "incident-classification", target: "airtable-incidents" },
  ],
};
