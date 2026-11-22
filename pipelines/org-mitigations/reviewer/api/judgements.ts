import { escapeFormulaString, listAllRecords } from "@api/_airtable";
import { readAirtableEnv, type WorkerEnv } from "@api/_env";
import { errorResponse, handleError } from "@api/_http";
import {
  JUDGEMENT_FIELDS,
  type JudgementFields,
  readJudgement,
} from "@api/_judgements";
import { userEmail } from "@api/_user";
import type { JudgementsResponse } from "@shared/judgements";

export default async function handler(
  request: Request,
  env: WorkerEnv,
): Promise<Response> {
  if (request.method !== "GET") {
    return errorResponse(405, "Method not allowed");
  }
  const email = userEmail(request, env);
  if (email === null) {
    return errorResponse(401, "No user is signed in");
  }
  try {
    const airtable = readAirtableEnv(env);
    const records = await listAllRecords<JudgementFields>(
      airtable.pat,
      airtable.baseId,
      airtable.judgementsTable,
      {
        filterByFormula: `{Reviewer}="${escapeFormulaString(email)}"`,
        fields: JUDGEMENT_FIELDS,
      },
    );
    const body: JudgementsResponse = {
      judgements: records.map(readJudgement),
    };
    return Response.json(body);
  } catch (error) {
    return handleError(error);
  }
}
