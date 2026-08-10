export interface AirtableRecord<F = Record<string, unknown>> {
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

interface ListOptions {
  view?: string;
  fields?: string[];
  filterByFormula?: string;
  pageSize?: number;
}

const AIRTABLE_BASE = "https://api.airtable.com/v0";

function authHeaders(pat: string): HeadersInit {
  return {
    Authorization: `Bearer ${pat}`,
    "Content-Type": "application/json",
  };
}

function buildListUrl(
  baseId: string,
  table: string,
  options: ListOptions,
  offset: string | undefined,
): string {
  const params = new URLSearchParams();
  if (options.view !== undefined) {
    params.set("view", options.view);
  }
  if (options.filterByFormula !== undefined) {
    params.set("filterByFormula", options.filterByFormula);
  }
  params.set("pageSize", String(options.pageSize ?? 100));
  if (options.fields !== undefined) {
    for (const field of options.fields) {
      params.append("fields[]", field);
    }
  }
  if (offset !== undefined) {
    params.set("offset", offset);
  }
  const path = `${AIRTABLE_BASE}/${baseId}/${encodeURIComponent(table)}`;
  return `${path}?${params.toString()}`;
}

export async function listAllRecords<F>(
  pat: string,
  baseId: string,
  table: string,
  options: ListOptions = {},
): Promise<AirtableRecord<F>[]> {
  const records: AirtableRecord<F>[] = [];
  let offset: string | undefined;
  do {
    const url = buildListUrl(baseId, table, options, offset);
    const response = await fetch(url, { headers: authHeaders(pat) });
    if (!response.ok) {
      throw new AirtableError(response.status, await response.text());
    }
    const data = (await response.json()) as ListResponse<F>;
    records.push(...data.records);
    offset = data.offset;
  } while (offset !== undefined);
  return records;
}

export async function getRecord<F>(
  pat: string,
  baseId: string,
  table: string,
  recordId: string,
): Promise<AirtableRecord<F>> {
  const url = `${AIRTABLE_BASE}/${baseId}/${encodeURIComponent(table)}/${recordId}`;
  const response = await fetch(url, { headers: authHeaders(pat) });
  if (!response.ok) {
    throw new AirtableError(response.status, await response.text());
  }
  return (await response.json()) as AirtableRecord<F>;
}

export interface RecordUpdate<F> {
  id: string;
  fields: F;
}

async function writeRecords<F>(
  pat: string,
  baseId: string,
  table: string,
  method: "POST" | "PATCH",
  records: { id?: string; fields: F }[],
): Promise<AirtableRecord<F>[]> {
  if (records.length === 0) {
    return [];
  }
  const url = `${AIRTABLE_BASE}/${baseId}/${encodeURIComponent(table)}`;
  const response = await fetch(url, {
    method,
    headers: authHeaders(pat),
    body: JSON.stringify({ records }),
  });
  if (!response.ok) {
    throw new AirtableError(response.status, await response.text());
  }
  const data = (await response.json()) as RecordsResponse<F>;
  return data.records;
}

export async function createRecords<F>(
  pat: string,
  baseId: string,
  table: string,
  rows: F[],
): Promise<AirtableRecord<F>[]> {
  const records = rows.map((fields) => ({ fields }));
  return await writeRecords(pat, baseId, table, "POST", records);
}

export async function updateRecords<F>(
  pat: string,
  baseId: string,
  table: string,
  records: RecordUpdate<F>[],
): Promise<AirtableRecord<F>[]> {
  return await writeRecords(pat, baseId, table, "PATCH", records);
}

export async function createRecord<F>(
  pat: string,
  baseId: string,
  table: string,
  fields: F,
): Promise<AirtableRecord<F>> {
  const records = await createRecords(pat, baseId, table, [fields]);
  return records[0];
}

export async function updateRecord<F>(
  pat: string,
  baseId: string,
  table: string,
  recordId: string,
  fields: F,
): Promise<AirtableRecord<F>> {
  const records = await updateRecords(pat, baseId, table, [
    { id: recordId, fields },
  ]);
  return records[0];
}

export async function deleteRecords(
  pat: string,
  baseId: string,
  table: string,
  recordIds: string[],
): Promise<void> {
  if (recordIds.length === 0) {
    return;
  }
  const params = new URLSearchParams();
  for (const id of recordIds) {
    params.append("records[]", id);
  }
  const url = `${AIRTABLE_BASE}/${baseId}/${encodeURIComponent(table)}?${params.toString()}`;
  const response = await fetch(url, {
    method: "DELETE",
    headers: authHeaders(pat),
  });
  if (!response.ok) {
    throw new AirtableError(response.status, await response.text());
  }
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

export function escapeFormulaString(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}
