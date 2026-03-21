import type { PipelineDefinition } from "@/types/pipeline";

export const pipeline: PipelineDefinition = {
  id: "actors",
  name: "Actors",
  description:
    "Classifies organizations by their role in the AI ecosystem (Developer, Deployer, Infrastructure Provider, etc.).",
  nodes: [
    {
      id: "actors-company-list",
      label: "Airtable: Companies",
      type: "datastore",
    },
    {
      id: "actors-classifier",
      label: "ai-actor-classifier",
      type: "processor",
    },
    {
      id: "actors-logo-processor",
      label: "airi-orgreview-logoprocessing",
      type: "processor",
    },
    {
      id: "actors-output",
      label: "Airtable: Companies (enriched)",
      type: "datastore",
    },
  ],
  edges: [
    { source: "actors-company-list", target: "actors-classifier" },
    { source: "actors-classifier", target: "actors-logo-processor" },
    { source: "actors-logo-processor", target: "actors-output" },
  ],
};
