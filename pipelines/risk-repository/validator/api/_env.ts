export interface AirtableEnv {
  pat: string;
  baseId: string;
  documentsTable: string;
  documentsView: string;
  decisionsTable: string;
  risksTable: string;
  reviewsTable: string;
  proposedExtractionsTable: string;
  fullTextTable: string;
}

export function readAirtableEnv(): AirtableEnv {
  const pat = required("AIRTABLE_PAT");
  const baseId = required("AIRTABLE_BASE_ID");
  const documentsTable = required("AIRTABLE_DOCUMENTS_TABLE");
  const documentsView = required("AIRTABLE_DOCUMENTS_VIEW");
  const decisionsTable = required("AIRTABLE_DECISIONS_TABLE");
  const risksTable = required("AIRTABLE_RISKS_TABLE");
  const reviewsTable = required("AIRTABLE_REVIEWS_TABLE");
  const proposedExtractionsTable = required(
    "AIRTABLE_PROPOSED_EXTRACTIONS_TABLE",
  );
  const fullTextTable = required("AIRTABLE_FULL_TEXT_TABLE");
  return {
    pat,
    baseId,
    documentsTable,
    documentsView,
    decisionsTable,
    risksTable,
    reviewsTable,
    proposedExtractionsTable,
    fullTextTable,
  };
}

function required(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}
