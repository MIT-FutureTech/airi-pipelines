import type { AirtableTable } from "@/airtable/types";

export const aiRiskDatabase: AirtableTable = {
  tableId: "tbla5iOE7OXyoqi49",
  name: "AI Risk Database",
  description:
    "The risk repository itself: one row per extracted AI risk, with the authors' description and taxonomy classifications. The extraction and classification stages that would populate it are proposed — they currently write local JSON, not Airtable.",
  fields: [
    {
      name: "Document_ID",
      type: "multipleRecordLinks",
      access: {
        "risk-extraction": {
          mode: "write",
          writtenAs: "link to the source document",
          notes: "Proposed.",
        },
      },
    },
    {
      name: "Description",
      type: "multilineText",
      access: {
        "risk-extraction": {
          mode: "write",
          writtenAs: "authors' risk description",
          notes:
            "Proposed. A close paraphrase of how the paper frames the risk.",
        },
      },
    },
    {
      name: "Risk category",
      type: "multilineText",
      access: {
        "risk-extraction": {
          mode: "write",
          writtenAs: "authors' category name",
          notes: "Proposed. Empty if the paper does not categorize the risk.",
        },
      },
    },
    {
      name: "Risk Subcategory",
      type: "multilineText",
      access: {
        "risk-extraction": {
          mode: "write",
          writtenAs: "authors' subcategory name",
          notes: "Proposed. Empty if the paper does not subcategorize.",
        },
      },
    },
    {
      name: "CausalTax_Entity",
      type: "multipleRecordLinks",
      access: {
        "risk-classification": {
          mode: "write",
          writtenAs: "human | AI | other",
          notes: "Proposed. Causal Taxonomy: the entity that causes the risk.",
        },
      },
    },
    {
      name: "CausalTax_Intent",
      type: "multipleRecordLinks",
      access: {
        "risk-classification": {
          mode: "write",
          writtenAs: "intentional | unintentional | other",
          notes:
            "Proposed. Causal Taxonomy: whether the risk is an expected or unexpected outcome.",
        },
      },
    },
    {
      name: "CausalTax_Timing",
      type: "multipleRecordLinks",
      access: {
        "risk-classification": {
          mode: "write",
          writtenAs: "pre-deployment | post-deployment | other",
          notes:
            "Proposed. Causal Taxonomy: the stage in the AI lifecycle when the risk occurs.",
        },
      },
    },
    {
      name: "Domain Category",
      type: "multipleRecordLinks",
      access: {},
    },
    {
      name: "Subdomain Category",
      type: "multipleRecordLinks",
      access: {},
    },
  ],
};
