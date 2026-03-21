import type { PipelineDefinition } from "@/types/pipeline";

export const pipeline: PipelineDefinition = {
  id: "incidents",
  name: "Incidents",
  description:
    "Would classify AI incidents from AIID into subdomains, causal factors, severity, and purpose. Currently data is manually entered in Airtable.",
  nodes: [
    {
      id: "aiid",
      label: "AIID (incidentdatabase.ai)",
      type: "external-service",
    },
    {
      id: "incident-scraper",
      label: "incident-scraper",
      type: "proposed",
    },
    {
      id: "airtable-incidents",
      label: "Airtable: Incidents",
      type: "datastore",
    },
    {
      id: "incident-classifier",
      label: "incident-classifier",
      type: "proposed",
    },
  ],
  shared: [],
  edges: [
    { source: "aiid", target: "incident-scraper" },
    { source: "incident-scraper", target: "airtable-incidents" },
    {
      source: "airtable-incidents",
      target: "incident-classifier",
      label: "currently manual",
    },
  ],
};
