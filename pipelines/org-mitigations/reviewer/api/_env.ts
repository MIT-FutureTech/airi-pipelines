export interface WorkerEnv {
  AIRTABLE_PAT?: string;
  AIRTABLE_BASE_ID?: string;
  AIRTABLE_JUDGEMENTS_TABLE?: string;
}

export interface AirtableEnv {
  pat: string;
  baseId: string;
  judgementsTable: string;
}

export function readAirtableEnv(env: WorkerEnv): AirtableEnv {
  return {
    pat: required(env, "AIRTABLE_PAT"),
    baseId: required(env, "AIRTABLE_BASE_ID"),
    judgementsTable: required(env, "AIRTABLE_JUDGEMENTS_TABLE"),
  };
}

function required(env: WorkerEnv, name: keyof WorkerEnv): string {
  const value = env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}
