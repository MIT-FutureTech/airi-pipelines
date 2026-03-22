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
      id: "incident-scraping",
      label: "Incident scraping",
      type: "proposed",
    },
    {
      id: "airtable-incidents",
      label: "Airtable: Incidents",
      type: "datastore",
    },
    {
      id: "incident-classification",
      label: "Incident classification",
      type: "proposed",
    },
  ],
  shared: [],
  edges: [
    { source: "aiid", target: "incident-scraping" },
    { source: "incident-scraping", target: "airtable-incidents" },
    {
      source: "airtable-incidents",
      target: "incident-classification",
      label: "currently manual",
    },
  ],
};
