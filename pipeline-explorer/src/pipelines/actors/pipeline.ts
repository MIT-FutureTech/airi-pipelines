import type { PipelineDefinition } from "@/types/pipeline";
import { airtableCompanies } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "actors",
  name: "Actors",
  description:
    "Classifies organizations by their role in the AI ecosystem (Developer, Deployer, Infrastructure Provider, etc.).",
  nodes: [
    {
      id: "actor-role-classification",
      label: "AI actor role classification",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/ai-actor-classifier",
        label: "ai-actor-classifier",
      },
    },
    {
      id: "logo-processing",
      label: "Logo processing",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgreview-logoprocessing",
        label: "airi-orgreview-logoprocessing",
      },
    },
    {
      id: "actors-output",
      label: "Airtable: Companies (enriched)",
      type: "datastore",
      verified: false,
    },
  ],
  shared: [airtableCompanies],
  edges: [
    { source: "airtable-companies", target: "actor-role-classification" },
    { source: "actor-role-classification", target: "logo-processing" },
    { source: "logo-processing", target: "actors-output" },
  ],
};
