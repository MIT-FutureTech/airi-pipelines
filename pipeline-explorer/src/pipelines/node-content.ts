import type { ComponentType } from "react";
import ActorRoleClassification from "./actors/actor-role-classification.mdx";
import LogoProcessing from "./actors/logo-processing.mdx";
import AgenticScreening from "./document-processing/agentic-screening.mdx";
import CompanyScraping from "./document-processing/company-scraping.mdx";
import DocTypeClassification from "./document-processing/doc-type-classification.mdx";
import FulltextExtraction from "./document-processing/fulltext-extraction.mdx";
import GreyLitSearch from "./document-processing/grey-lit-search.mdx";
import RelevanceScreening from "./document-processing/relevance-screening.mdx";
import MitigationClassificationCorporate from "./mitigations/mitigation-classification-corporate.mdx";
import MitigationTaxonomyClassification from "./mitigations/mitigation-taxonomy-classification.mdx";
import SystematicLitReview from "./mitigations/systematic-lit-review.mdx";
import RiskClassification from "./risks/risk-classification.mdx";
import PdfKeywordExtraction from "./shared/pdf-keyword-extraction.mdx";

const nodeContent: Record<string, ComponentType> = {
  "pdf-keyword-extraction": PdfKeywordExtraction,

  "grey-lit-search": GreyLitSearch,
  "company-scraping": CompanyScraping,
  "fulltext-extraction": FulltextExtraction,
  "relevance-screening": RelevanceScreening,
  "agentic-screening": AgenticScreening,
  "doc-type-classification": DocTypeClassification,

  "actor-role-classification": ActorRoleClassification,
  "logo-processing": LogoProcessing,

  "risk-classification": RiskClassification,

  "mitigation-classification-corporate": MitigationClassificationCorporate,
  "systematic-lit-review": SystematicLitReview,
  "mitigation-taxonomy-classification": MitigationTaxonomyClassification,
};

export function getNodeContent(nodeId: string): ComponentType | null {
  return nodeContent[nodeId] ?? null;
}
