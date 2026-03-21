import type { ComponentType } from "react";

// Registry mapping node IDs to their MDX content components.
// When adding a new MDX file, import it here and add it to the map.

// Actors pipeline
import ActorsClassifier from "./actors/actors-classifier.mdx";
import ActorsLogoProcessor from "./actors/actors-logo-processor.mdx";
import AgenticFramework from "./document-processing/agentic-framework.mdx";
import FulltextExtractor from "./document-processing/fulltext-extractor.mdx";
// Document Processing pipeline
import Greylitsearcher from "./document-processing/greylitsearcher.mdx";
import OrgDocClassifier from "./document-processing/org-doc-classifier.mdx";
import OrgrevOrglist from "./document-processing/orgrev-orglist.mdx";
import ScreeningOrchestrator from "./document-processing/screening-orchestrator.mdx";
// Risks pipeline
import RisksClassifier from "./risks/risks-classifier.mdx";
import RisksPdfAnalysis from "./risks/risks-pdf-analysis.mdx";

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

  // Risks
  "risks-pdf-analysis": RisksPdfAnalysis,
  "risks-classifier": RisksClassifier,
};

export function getNodeContent(nodeId: string): ComponentType | null {
  return nodeContent[nodeId] ?? null;
}
