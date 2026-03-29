import type { AirtableBase } from "@/airtable/types";
import { includedDocuments } from "./included-documents";
import { organizationActorRole } from "./organization-actor-role";
import { organizationMetadata } from "./organization-metadata";
import { screeningPrompts } from "./screening-prompts";
import { searchResults } from "./search-results";
import { secFilings } from "./sec-filings";

export const organisationalReview: AirtableBase = {
  baseId: "appHrhJQHkZz4c82U",
  name: "AI Risk Organisational Review",
  tables: [
    searchResults,
    screeningPrompts,
    organizationMetadata,
    organizationActorRole,
    includedDocuments,
    secFilings,
  ],
};
