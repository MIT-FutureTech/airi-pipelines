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
      id: "governance-scraper",
      label: "governance-scraper",
      type: "proposed",
    },
    {
      id: "airtable-governance",
      label: "Airtable: Governance",
      type: "datastore",
    },
    {
      id: "governance-classifier",
      label: "governance-classifier",
      type: "proposed",
    },
  ],
  shared: [],
  edges: [
    { source: "governance-sources", target: "governance-scraper" },
    {
      source: "governance-scraper",
      target: "airtable-governance",
    },
    {
      source: "airtable-governance",
      target: "governance-classifier",
      label: "currently manual",
    },
  ],
};
