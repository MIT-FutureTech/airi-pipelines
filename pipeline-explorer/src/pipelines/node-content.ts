import type { ComponentType } from "react";

import ActorsClassifier from "./actors/actors-classifier.mdx";
import ActorsLogoProcessor from "./actors/actors-logo-processor.mdx";
import AgenticFramework from "./document-processing/agentic-framework.mdx";
import FulltextExtractor from "./document-processing/fulltext-extractor.mdx";
import Greylitsearcher from "./document-processing/greylitsearcher.mdx";
import OrgDocClassifier from "./document-processing/org-doc-classifier.mdx";
import OrgrevOrglist from "./document-processing/orgrev-orglist.mdx";
import ScreeningOrchestrator from "./document-processing/screening-orchestrator.mdx";
import MitigationsClassifier from "./mitigations/mitigations-classifier.mdx";
import MitigationsCorpClassifier from "./mitigations/mitigations-corp-classifier.mdx";
import MitigationsReview from "./mitigations/mitigations-review.mdx";
import RisksClassifier from "./risks/risks-classifier.mdx";
import CorporatePdfAnalysis from "./shared/corporate-pdf-analysis.mdx";

const nodeContent: Record<string, ComponentType> = {
  "corporate-pdf-analysis": CorporatePdfAnalysis,

  greylitsearcher: Greylitsearcher,
  "orgrev-orglist": OrgrevOrglist,
  "fulltext-extractor": FulltextExtractor,
  "screening-orchestrator": ScreeningOrchestrator,
  "agentic-framework": AgenticFramework,
  "org-doc-classifier": OrgDocClassifier,

  "actors-classifier": ActorsClassifier,
  "actors-logo-processor": ActorsLogoProcessor,

  "risks-classifier": RisksClassifier,

  "mitigations-corp-classifier": MitigationsCorpClassifier,
  "mitigations-review": MitigationsReview,
  "mitigations-classifier": MitigationsClassifier,
};

export function getNodeContent(nodeId: string): ComponentType | null {
  return nodeContent[nodeId] ?? null;
}
