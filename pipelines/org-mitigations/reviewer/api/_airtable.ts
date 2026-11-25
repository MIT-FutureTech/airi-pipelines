export interface AirtableRecord<F> {
  id: string;
  createdTime: string;
  fields: F;
}

interface ListResponse<F> {
  records: AirtableRecord<F>[];
  offset?: string;
}

interface RecordsResponse<F> {
  records: AirtableRecord<F>[];
}

export interface ListOptions {
  filterByFormula?: string;
  fields?: string[];
}

export class AirtableError extends Error {
  status: number;
  body: string;
  constructor(status: number, body: string) {
    super(`Airtable request failed: HTTP ${status} ${body}`);
    this.status = status;
    this.body = body;
  }
}

const AIRTABLE_BASE = "https://api.airtable.com/v0";
const PAGE_SIZE = 100;

const RATE_LIMITED = 429;
const MAX_RATE_LIMIT_RETRIES = 3;
const BASE_RETRY_DELAY_MS = 250;
const MAX_RETRY_DELAY_MS = 2000;

export async function listAllRecords<F>(
  pat: string,
  baseId: string,
  table: string,
  options: ListOptions,
): Promise<AirtableRecord<F>[]> {
  const records: AirtableRecord<F>[] = [];
  let offset: string | undefined;
  do {
    const url = listUrl(baseId, table, options, offset);
    const response = await airtableFetch(url, { headers: authHeaders(pat) });
    if (!response.ok) {
      throw new AirtableError(response.status, await response.text());
    }
    const data = (await response.json()) as ListResponse<F>;
    records.push(...data.records);
    offset = data.offset;
  } while (offset !== undefined);
  return records;
}

// Creates the record, or updates the one whose fieldsToMergeOn match it.
export async function upsertRecord<F>(
  pat: string,
  baseId: string,
  table: string,
  fieldsToMergeOn: string[],
  fields: F,
): Promise<AirtableRecord<F>> {
  const response = await airtableFetch(tableUrl(baseId, table), {
    method: "PATCH",
    headers: authHeaders(pat),
    body: JSON.stringify({
      performUpsert: { fieldsToMergeOn },
      records: [{ fields }],
    }),
  });
  if (!response.ok) {
    throw new AirtableError(response.status, await response.text());
  }
  const data = (await response.json()) as RecordsResponse<F>;
  return data.records[0];
}

export function escapeFormulaString(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function tableUrl(baseId: string, table: string): string {
  return `${AIRTABLE_BASE}/${baseId}/${encodeURIComponent(table)}`;
}

function listUrl(
  baseId: string,
  table: string,
  options: ListOptions,
  offset: string | undefined,
): string {
  const params = new URLSearchParams();
  params.set("pageSize", String(PAGE_SIZE));
  if (options.filterByFormula !== undefined) {
    params.set("filterByFormula", options.filterByFormula);
  }
  for (const field of options.fields ?? []) {
    params.append("fields[]", field);
  }
  if (offset !== undefined) {
    params.set("offset", offset);
  }
  return `${tableUrl(baseId, table)}?${params.toString()}`;
}

function authHeaders(pat: string): HeadersInit {
  return {
    Authorization: `Bearer ${pat}`,
    "Content-Type": "application/json",
  };
}

async function airtableFetch(
  url: string,
  init: RequestInit,
): Promise<Response> {
  let response = await fetch(url, init);
  for (
    let retry = 0;
    response.status === RATE_LIMITED && retry < MAX_RATE_LIMIT_RETRIES;
    retry += 1
  ) {
    const delay = retryDelayMs(response, retry);
    console.warn(`Airtable rate limited ${url}; retrying in ${delay}ms`);
    await new Promise((resolve) => setTimeout(resolve, delay));
    response = await fetch(url, init);
  }
  return response;
}

function retryDelayMs(response: Response, retry: number): number {
  const retryAfter = Number(response.headers.get("retry-after"));
  if (Number.isFinite(retryAfter) && retryAfter > 0) {
    return Math.min(retryAfter * 1000, MAX_RETRY_DELAY_MS);
  }
  return Math.min(BASE_RETRY_DELAY_MS * 2 ** retry, MAX_RETRY_DELAY_MS);
}
