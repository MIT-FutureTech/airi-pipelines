import type { AirtableRecord } from "@api/_airtable";
import { DECISIONS, type Decision, type Judgement } from "@shared/judgements";

export interface JudgementFields {
  Key?: string;
  Company?: string[];
  Code?: string[];
  Reviewer?: string;
  Decision?: string;
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
      fields.Decision === undefined ? null : readDecision(fields.Decision),
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
