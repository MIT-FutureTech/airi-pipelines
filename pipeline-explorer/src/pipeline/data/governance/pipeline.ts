import type { PipelineDefinition } from "@/pipeline/types";

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
      verified: false,
    },
    {
      id: "governance-scraping",
      label: "Governance document scraping",
      type: "proposed",
      verified: false,
    },
    {
      id: "airtable-governance",
      label: "Airtable: Governance",
      type: "datastore",
      verified: false,
    },
    {
      id: "governance-classification",
      label: "Governance classification",
      type: "proposed",
      verified: false,
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
