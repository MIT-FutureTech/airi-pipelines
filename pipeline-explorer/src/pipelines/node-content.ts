import type { ComponentType } from "react";

// Registry mapping node IDs to their MDX content components.
// When adding a new MDX file, import it here and add it to the map.

// Document Processing pipeline
import Greylitsearcher from "./document-processing/greylitsearcher.mdx";
import OrgrevOrglist from "./document-processing/orgrev-orglist.mdx";
import FulltextExtractor from "./document-processing/fulltext-extractor.mdx";
import ScreeningOrchestrator from "./document-processing/screening-orchestrator.mdx";
import AgenticFramework from "./document-processing/agentic-framework.mdx";
import OrgDocClassifier from "./document-processing/org-doc-classifier.mdx";

// Actors pipeline
import ActorsClassifier from "./actors/actors-classifier.mdx";
import ActorsLogoProcessor from "./actors/actors-logo-processor.mdx";

const nodeContent: Record<string, ComponentType> = {
  // Document Processing
  greylitsearcher: Greylitsearcher,
  "orgrev-orglist": OrgrevOrglist,
  "fulltext-extractor": FulltextExtractor,
  "screening-orchestrator": ScreeningOrchestrator,
  "agentic-framework": AgenticFramework,
  "org-doc-classifier": OrgDocClassifier,

  // Actors
  "actors-classifier": ActorsClassifier,
  "actors-logo-processor": ActorsLogoProcessor,
};

export function getNodeContent(nodeId: string): ComponentType | null {
  return nodeContent[nodeId] ?? null;
}
