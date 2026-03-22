import type { PipelineDefinition } from "@/types/pipeline";

export const pipeline: PipelineDefinition = {
  id: "governance",
  name: "Governance",
  description:
    "Would classify governance documents (regulations, policies, frameworks) into risk subdomains, lifecycle stages, actor types, and sectors. Currently data is manually entered in Airtable.",
  nodes: [
    {
      id: "governance-sources",
      label: "Government sources",
      type: "external-service",
    },
    {
      id: "governance-scraping",
      label: "Governance document scraping",
      type: "proposed",
    },
    {
      id: "airtable-governance",
      label: "Airtable: Governance",
      type: "datastore",
    },
    {
      id: "governance-classification",
      label: "Governance classification",
      type: "proposed",
    },
  ],
  shared: [],
  edges: [
    { source: "governance-sources", target: "governance-scraping" },
    { source: "governance-scraping", target: "airtable-governance" },
    {
      source: "airtable-governance",
      target: "governance-classification",
      label: "currently manual",
    },
  ],
};
