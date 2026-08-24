export interface WorkerEnv {
  AIRTABLE_PAT?: string;
  AIRTABLE_BASE_ID?: string;
  AIRTABLE_DOCUMENTS_TABLE?: string;
  AIRTABLE_DOCUMENTS_VIEW?: string;
  AIRTABLE_DECISIONS_TABLE?: string;
  AIRTABLE_RISKS_TABLE?: string;
  AIRTABLE_REVIEWS_TABLE?: string;
  AIRTABLE_PROPOSED_EXTRACTIONS_TABLE?: string;
  AIRTABLE_FULL_TEXT_TABLE?: string;
}

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

export function readAirtableEnv(env: WorkerEnv): AirtableEnv {
  return {
    pat: required(env, "AIRTABLE_PAT"),
    baseId: required(env, "AIRTABLE_BASE_ID"),
    documentsTable: required(env, "AIRTABLE_DOCUMENTS_TABLE"),
    documentsView: required(env, "AIRTABLE_DOCUMENTS_VIEW"),
    decisionsTable: required(env, "AIRTABLE_DECISIONS_TABLE"),
    risksTable: required(env, "AIRTABLE_RISKS_TABLE"),
    reviewsTable: required(env, "AIRTABLE_REVIEWS_TABLE"),
    proposedExtractionsTable: required(
      env,
      "AIRTABLE_PROPOSED_EXTRACTIONS_TABLE",
    ),
    fullTextTable: required(env, "AIRTABLE_FULL_TEXT_TABLE"),
  };
}

function required(env: WorkerEnv, name: keyof WorkerEnv): string {
  const value = env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}
