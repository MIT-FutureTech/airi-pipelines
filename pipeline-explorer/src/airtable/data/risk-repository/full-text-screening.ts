import type { AirtableTable } from "@/airtable/types";

export const fullTextScreening: AirtableTable = {
  tableId: "tblNcpINE96SXqgzi",
  name: "Full-Text Screening",
  description:
    "Stage-2 full-text screening. Holds documents promoted from abstract screening, each with the full-text PDF attached, plus the LLM relevance score and human review columns.",
  fields: [
    {
      name: "full_text_pdf",
      type: "multipleAttachments",
      access: {
        "full-text-screening": {
          mode: "read",
          notes:
            "The attached PDF is converted to Markdown and screened as the full text.",
        },
        "risk-extraction": {
          mode: "read",
          notes: "Proposed: the same PDF is the source for risk extraction.",
        },
      },
    },
    {
      name: "has_full_text_pdf",
      type: "formula",
      access: {
        "full-text-screening": {
          mode: "read",
          filterFormula: "{has_full_text_pdf} = TRUE()",
          notes: "Records without an attached PDF are skipped.",
        },
      },
    },
    {
      name: "llm_relevance_score",
      type: "number",
      access: {
        "full-text-screening": {
          mode: "write",
          writtenAs: "predicted include count (0–10)",
          notes:
            "The LLM's estimate of how many of ten human reviewers would include the document.",
        },
      },
    },
    {
      name: "llm_reasoning",
      type: "multilineText",
      access: {
        "full-text-screening": {
          mode: "write",
          writtenAs: "criteria breakdown",
        },
      },
    },
    {
      name: "screening_model_version",
      type: "singleLineText",
      access: {
        "full-text-screening": {
          mode: "write",
          writtenAs: "e.g. openai/gpt-5-mini",
        },
      },
    },
    {
      name: "text_source",
      type: "singleSelect",
      access: {
        "full-text-screening": { mode: "write", writtenAs: "full_text" },
      },
    },
    {
      name: "screening_status",
      type: "singleSelect",
      access: {
        "full-text-screening": { mode: "write", writtenAs: "screened" },
      },
    },
    {
      name: "screened_at",
      type: "dateTime",
      access: {
        "full-text-screening": { mode: "write", writtenAs: "run timestamp" },
      },
    },
  ],
};
