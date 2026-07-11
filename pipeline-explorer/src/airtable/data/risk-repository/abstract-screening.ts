import type { AirtableTable } from "@/airtable/types";

export const abstractScreening: AirtableTable = {
  tableId: "tblvzGVOuHBFfYlyg",
  name: "Abstract Screening",
  description:
    "Stage-1 title+abstract screening of the full corpus. One row per document, holding the aggregated LLM include/exclude decision and screening metadata. Documents that pass advance to Full-Text Screening.",
  fields: [
    {
      name: "title",
      type: "singleLineText",
      access: {
        "abstract-screening": {
          mode: "read",
          notes: "Screened as the document title.",
        },
      },
    },
    {
      name: "abstract",
      type: "multilineText",
      access: {
        "abstract-screening": {
          mode: "read",
          notes: "The abstract text shown to the LLM screener.",
        },
      },
    },
    {
      name: "llm_include",
      type: "singleSelect",
      access: {
        "abstract-screening": {
          mode: "write",
          writtenAs: "include | exclude | uncertain",
        },
      },
    },
    {
      name: "llm_reasoning",
      type: "multilineText",
      access: {
        "abstract-screening": {
          mode: "write",
          writtenAs: "criteria breakdown",
          notes: "The LLM's per-criterion reasoning behind the decision.",
        },
      },
    },
    {
      name: "n_screens",
      type: "number",
      access: {
        "abstract-screening": { mode: "write", writtenAs: "1" },
      },
    },
    {
      name: "n_include",
      type: "number",
      access: {
        "abstract-screening": {
          mode: "write",
          writtenAs: "1 if included, else 0",
        },
      },
    },
    {
      name: "decision_rule",
      type: "singleLineText",
      access: {
        "abstract-screening": {
          mode: "write",
          writtenAs: "Single abstract screen",
        },
      },
    },
    {
      name: "screening_model_version",
      type: "singleLineText",
      access: {
        "abstract-screening": {
          mode: "write",
          writtenAs: "e.g. openai/gpt-5-mini",
        },
      },
    },
    {
      name: "screening_prompt_version",
      type: "singleLineText",
      access: {
        "abstract-screening": {
          mode: "write",
          notes: "Recorded when a prompt version label is supplied.",
        },
      },
    },
    {
      name: "text_source",
      type: "singleSelect",
      access: {
        "abstract-screening": { mode: "write", writtenAs: "abstract" },
      },
    },
    {
      name: "screening_status",
      type: "singleSelect",
      access: {
        "abstract-screening": { mode: "write", writtenAs: "screened" },
      },
    },
    {
      name: "screened_at",
      type: "dateTime",
      access: {
        "abstract-screening": { mode: "write", writtenAs: "run timestamp" },
      },
    },
  ],
};
