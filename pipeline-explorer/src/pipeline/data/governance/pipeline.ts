import type { PipelineDefinition } from "@/pipeline/types";

export const pipeline: PipelineDefinition = {
  id: "governance",
  name: "Governance",
  description:
    "Classifies governance documents (regulations, policies, frameworks) into risk subdomains, lifecycle stages, actor types, and sectors. Input is the AGORA dataset. Pipeline repos live in a separate GitHub org.",
  nodes: [
    {
      id: "agora",
      label: "AGORA dataset",
      type: "external-service",
      verified: false,
      link: { url: "https://agora.eto.tech/", label: "agora.eto.tech" },
    },
    {
      id: "governance-ingestion",
      label: "Governance ingestion",
      type: "processor",
      verified: false,
    },
    {
      id: "governance-classification",
      label: "LLM governance classification",
      type: "processor",
      verified: false,
    },
    {
      id: "airtable-governance",
      label: "Airtable: Governance Mapping",
      type: "datastore",
      verified: false,
    },
  ],
  shared: [],
  edges: [
    { source: "agora", target: "governance-ingestion" },
    { source: "governance-ingestion", target: "governance-classification" },
    { source: "governance-classification", target: "airtable-governance" },
  ],
};
