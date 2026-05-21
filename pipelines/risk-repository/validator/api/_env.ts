interface AirtableEnv {
  pat: string;
  baseId: string;
  documentsTable: string;
  documentsView: string;
  validationsTable: string;
}

export function readAirtableEnv(): AirtableEnv {
  const pat = required("AIRTABLE_PAT");
  const baseId = required("AIRTABLE_BASE_ID");
  const documentsTable = required("AIRTABLE_DOCUMENTS_TABLE");
  const documentsView = required("AIRTABLE_DOCUMENTS_VIEW");
  const validationsTable = required("AIRTABLE_VALIDATIONS_TABLE");
  return { pat, baseId, documentsTable, documentsView, validationsTable };
}

function required(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}
