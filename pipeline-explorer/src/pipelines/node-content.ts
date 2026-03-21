import type { ComponentType } from "react";

// Registry mapping node IDs to their MDX content components.
// When adding a new MDX file, import it here and add it to the map.

import Scraper from "./example-pipeline/scraper.mdx";
import Classifier from "./example-pipeline/classifier.mdx";

// Document Processing pipeline
import Greylitsearcher from "./document-processing/greylitsearcher.mdx";
import OrgrevOrglist from "./document-processing/orgrev-orglist.mdx";
import FulltextExtractor from "./document-processing/fulltext-extractor.mdx";
import ScreeningOrchestrator from "./document-processing/screening-orchestrator.mdx";
import AgenticFramework from "./document-processing/agentic-framework.mdx";
import OrgDocClassifier from "./document-processing/org-doc-classifier.mdx";

const nodeContent: Record<string, ComponentType> = {
  scraper: Scraper,
  classifier: Classifier,

  // Document Processing
  greylitsearcher: Greylitsearcher,
  "orgrev-orglist": OrgrevOrglist,
  "fulltext-extractor": FulltextExtractor,
  "screening-orchestrator": ScreeningOrchestrator,
  "agentic-framework": AgenticFramework,
  "org-doc-classifier": OrgDocClassifier,
};

export function getNodeContent(nodeId: string): ComponentType | null {
  return nodeContent[nodeId] ?? null;
}
