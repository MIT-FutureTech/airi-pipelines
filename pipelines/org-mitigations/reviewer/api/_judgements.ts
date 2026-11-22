import type { AirtableRecord } from "@api/_airtable";
import {
  DECISIONS,
  type Decision,
  type Judgement,
  type SaveJudgementRequest,
} from "@shared/judgements";

export interface JudgementFields {
  Key?: string;
  Company?: string[];
  Code?: string[];
  Reviewer?: string;
  Decision?: string | null;
  Comment?: string;
  "Supporting mitigations"?: string[];
}

export const JUDGEMENT_FIELDS: (keyof JudgementFields)[] = [
  "Company",
  "Code",
  "Decision",
  "Comment",
  "Supporting mitigations",
];

const DECISION_VALUES: Record<Decision, string> = {
  yes: "Yes",
  no: "No",
  unsure: "Unsure",
};

export function readJudgement(
  record: AirtableRecord<JudgementFields>,
): Judgement {
  const { fields } = record;
  return {
    companyId: onlyLink(record, "Company", fields.Company),
    codeRecordId: onlyLink(record, "Code", fields.Code),
    decision:
      fields.Decision === undefined || fields.Decision === null
        ? null
        : readDecision(fields.Decision),
    comment: fields.Comment ?? "",
    supportingMitigationRecordIds: fields["Supporting mitigations"] ?? [],
  };
}

function onlyLink(
  record: AirtableRecord<JudgementFields>,
  field: string,
  recordIds: string[] | undefined,
): string {
  if (recordIds === undefined || recordIds.length !== 1) {
    throw new Error(
      `Judgement ${record.id} should link to one ${field}, not ${recordIds?.length ?? 0}`,
    );
  }
  return recordIds[0];
}

function readDecision(value: string): Decision {
  const decision = DECISIONS.find(
    (candidate) => DECISION_VALUES[candidate] === value,
  );
  if (decision === undefined) {
    throw new Error(`Unknown decision ${value}`);
  }
  return decision;
}

export function judgementFields(
  request: SaveJudgementRequest,
  email: string,
): JudgementFields {
  return {
    Key: `${request.companyName} · ${request.codeKey} · ${email}`,
    Company: [request.companyId],
    Code: [request.codeRecordId],
    Reviewer: email,
    Decision:
      request.decision === null ? null : DECISION_VALUES[request.decision],
    Comment: request.comment,
    "Supporting mitigations": request.supportingMitigationRecordIds,
  };
}

export function parseSaveRequest(body: unknown): SaveJudgementRequest | null {
  if (typeof body !== "object" || body === null) {
    return null;
  }
  const {
    companyId,
    companyName,
    codeRecordId,
    codeKey,
    decision,
    comment,
    supportingMitigationRecordIds,
  } = body as Record<string, unknown>;
  if (
    !isFilledString(companyId) ||
    !isFilledString(companyName) ||
    !isFilledString(codeRecordId) ||
    !isFilledString(codeKey) ||
    !(decision === null || isDecision(decision)) ||
    typeof comment !== "string" ||
    !Array.isArray(supportingMitigationRecordIds) ||
    !supportingMitigationRecordIds.every(isFilledString)
  ) {
    return null;
  }
  return {
    companyId,
    companyName,
    codeRecordId,
    codeKey,
    decision,
    comment,
    supportingMitigationRecordIds,
  };
}

function isDecision(value: unknown): value is Decision {
  return DECISIONS.some((decision) => decision === value);
}

function isFilledString(value: unknown): value is string {
  return typeof value === "string" && value !== "";
}
