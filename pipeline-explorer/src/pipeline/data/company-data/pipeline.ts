import type { PipelineDefinition } from "@/pipeline/types";
import { airtableCompanies } from "../shared/nodes";

export const pipeline: PipelineDefinition = {
  id: "company-data",
  name: "Company Data",
  description:
    "Scrapes and maintains the organization list from companiesmarketcap.com. Feeds into the Actors pipeline.",
  nodes: [
    {
      id: "companiesmarketcap",
      label: "companiesmarketcap.com",
      type: "external-service",
      verified: false,
    },
    {
      id: "company-scraping",
      label: "Company scraping",
      type: "processor",
      verified: false,
      link: {
        url: "https://github.com/MIT-FutureTech/airi-orgrev-orglist",
        label: "airi-orgrev-orglist",
      },
    },
    airtableCompanies,
  ],
  shared: [],
  edges: [
    { source: "companiesmarketcap", target: "company-scraping" },
    { source: "company-scraping", target: "airtable-companies" },
  ],
};
