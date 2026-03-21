import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "actors",
  name: "Actors",
  description:
    "Classifies organizations by their role in the AI ecosystem (Developer, Deployer, Infrastructure Provider, etc.).",
  nodes: [
    {
      id: "actors-classifier",
      label: "AI actor role classification",
      type: "processor",
    },
    {
      id: "actors-logo-processor",
      label: "Logo processing",
      type: "processor",
    },
    {
      id: "actors-output",
      label: "Airtable: Companies (enriched)",
      type: "datastore",
    },
  ],
  shared: [airtableCompanies],
  edges: [
    { source: "airtable-companies", target: "actors-classifier" },
    { source: "actors-classifier", target: "actors-logo-processor" },
    { source: "actors-logo-processor", target: "actors-output" },
  ],
};
