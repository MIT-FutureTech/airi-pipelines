import type { PipelineDefinition } from "@/types/pipeline";

export const pipeline: PipelineDefinition = {
  id: "example-pipeline",
  name: "Example Pipeline",
  description: "A placeholder pipeline to test the framework.",
  nodes: [
    {
      id: "data-source",
      label: "Data Source",
      type: "external-service",
      position: { x: 0, y: 0 },
    },
    {
      id: "scraper",
      label: "scraper-tool",
      type: "repo",
      position: { x: 0, y: 150 },
    },
    {
      id: "database",
      label: "Airtable: Records",
      type: "datastore",
      position: { x: 0, y: 300 },
    },
    {
      id: "classifier",
      label: "classifier-tool",
      type: "repo",
      position: { x: 0, y: 450 },
    },
    {
      id: "review",
      label: "Manual Review",
      type: "manual-step",
      position: { x: 200, y: 450 },
    },
    {
      id: "future-tool",
      label: "future-automation",
      type: "proposed",
      position: { x: 200, y: 300 },
    },
  ],
  edges: [
    { source: "data-source", target: "scraper" },
    { source: "scraper", target: "database" },
    { source: "database", target: "classifier" },
    { source: "database", target: "review", label: "low confidence" },
    { source: "future-tool", target: "database" },
  ],
};
