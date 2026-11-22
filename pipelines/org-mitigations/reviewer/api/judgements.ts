import {
  escapeFormulaString,
  listAllRecords,
  upsertRecord,
} from "@api/_airtable";
import { type AirtableEnv, readAirtableEnv, type WorkerEnv } from "@api/_env";
import { errorResponse, handleError } from "@api/_http";
import {
  JUDGEMENT_FIELDS,
  type JudgementFields,
  judgementFields,
  parseSaveRequest,
  readJudgement,
} from "@api/_judgements";
import { userEmail } from "@api/_user";
import type { Judgement, JudgementsResponse } from "@shared/judgements";

export default async function handler(
  request: Request,
  env: WorkerEnv,
): Promise<Response> {
  if (request.method !== "GET" && request.method !== "PUT") {
    return errorResponse(405, "Method not allowed");
  }
  const email = userEmail(request, env);
  if (email === null) {
    return errorResponse(401, "No user is signed in");
  }
  try {
    const airtable = readAirtableEnv(env);
    if (request.method === "GET") {
      return await listJudgements(airtable, email);
    }
    return await saveJudgement(airtable, email, request);
  } catch (error) {
    return handleError(error);
  }
}

async function listJudgements(
  airtable: AirtableEnv,
  email: string,
): Promise<Response> {
  const records = await listAllRecords<JudgementFields>(
    airtable.pat,
    airtable.baseId,
    airtable.judgementsTable,
    {
      filterByFormula: `{Reviewer}="${escapeFormulaString(email)}"`,
      fields: JUDGEMENT_FIELDS,
    },
  );
  const body: JudgementsResponse = { judgements: records.map(readJudgement) };
  return Response.json(body);
}

async function saveJudgement(
  airtable: AirtableEnv,
  email: string,
  request: Request,
): Promise<Response> {
  const save = parseSaveRequest(await request.json().catch(() => null));
  if (save === null) {
    return errorResponse(400, "Invalid judgement");
  }
  const record = await upsertRecord(
    airtable.pat,
    airtable.baseId,
    airtable.judgementsTable,
    ["Key"],
    judgementFields(save, email),
  );
  const body: Judgement = readJudgement(record);
  return Response.json(body);
}
