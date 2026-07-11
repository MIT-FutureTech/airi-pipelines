import type { PipelineDefinition } from "@/pipeline/types";

const RISK_REPO_SRC =
  "https://github.com/MIT-FutureTech/airi-pipelines/tree/main/pipelines/risk-repository/src/risk_repository";

const abstractScreeningTable =
  "https://airtable.com/app32FOUBa5WcUfEO/tblvzGVOuHBFfYlyg";
const fullTextScreeningTable =
  "https://airtable.com/app32FOUBa5WcUfEO/tblNcpINE96SXqgzi";
const riskDatabaseTable =
  "https://airtable.com/app32FOUBa5WcUfEO/tbla5iOE7OXyoqi49";

export const pipeline: PipelineDefinition = {
  id: "risk-repository",
  name: "Risk Repository",
  description:
    "Screens academic papers for AI-risk relevance, then extracts and classifies the individual risks they describe. Feeds the AI Risk Repository (airisk.mit.edu).",
  nodes: [
    {
      id: "rr-abstract-input",
      label: "Airtable: Abstract Screening",
      type: "datastore",
      verified: false,
      link: { url: abstractScreeningTable, label: "Open in Airtable" },
    },
    {
      id: "rr-abstract-screening",
      label: "Abstract screening",
      type: "processor",
      verified: true,
      link: {
        url: `${RISK_REPO_SRC}/screen.py`,
        label: "risk_repository/screen.py",
      },
    },
    {
      id: "rr-abstract-output",
      label: "Airtable: Abstract Screening",
      type: "datastore",
      verified: false,
      link: { url: abstractScreeningTable, label: "Open in Airtable" },
    },
    {
      id: "rr-full-text-screening",
      label: "Full-text screening",
      type: "processor",
      verified: false,
      link: {
        url: `${RISK_REPO_SRC}/screen.py`,
        label: "risk_repository/screen.py",
      },
    },
    {
      id: "rr-full-text-store",
      label: "Airtable: Full-Text Screening",
      type: "datastore",
      verified: false,
      link: { url: fullTextScreeningTable, label: "Open in Airtable" },
    },
    {
      id: "rr-risk-extraction",
      label: "Risk extraction",
      type: "proposed",
      verified: false,
      link: {
        url: `${RISK_REPO_SRC}/extract.py`,
        label: "risk_repository/extract.py",
      },
    },
    {
      id: "rr-risks-extracted",
      label: "Airtable: Risks",
      type: "proposed",
      verified: false,
      link: { url: riskDatabaseTable, label: "Open in Airtable" },
    },
    {
      id: "rr-risk-classification",
      label: "Risk classification",
      type: "proposed",
      verified: false,
      link: {
        url: `${RISK_REPO_SRC}/classify.py`,
        label: "risk_repository/classify.py",
      },
    },
    {
      id: "rr-risks-classified",
      label: "Airtable: Risks",
      type: "proposed",
      verified: false,
      link: { url: riskDatabaseTable, label: "Open in Airtable" },
    },
  ],
  shared: [],
  edges: [
    {
      source: "rr-abstract-input",
      target: "rr-abstract-screening",
      label: "abstracts",
    },
    {
      source: "rr-abstract-screening",
      target: "rr-abstract-output",
      label: "decisions",
    },
    {
      source: "rr-abstract-output",
      target: "rr-full-text-screening",
      label: "PDFs",
    },
    {
      source: "rr-full-text-screening",
      target: "rr-full-text-store",
      label: "decisions",
    },
    {
      source: "rr-full-text-store",
      target: "rr-risk-extraction",
      label: "PDFs",
    },
    {
      source: "rr-risk-extraction",
      target: "rr-risks-extracted",
      label: "risks",
    },
    {
      source: "rr-risks-extracted",
      target: "rr-risk-classification",
      label: "risks",
    },
    {
      source: "rr-risk-classification",
      target: "rr-risks-classified",
      label: "classifications",
    },
  ],
};
