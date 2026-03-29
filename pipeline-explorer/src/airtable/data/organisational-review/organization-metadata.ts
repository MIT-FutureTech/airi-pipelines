import type { AirtableTable } from "@/airtable/types";

export const organizationMetadata: AirtableTable = {
  tableId: "tblurwszwgrluMLrB",
  name: "Organization Metadata",
  fields: [
    {
      name: "cmc_company_name",
      type: "singleLineText",
      access: {
        "agentic-framework": {
          mode: "read",
          filterFormula: "{cmc_company_name} = '...'",
        },
        "airi-orgrev-orglist": { mode: "read" },
      },
    },
    {
      name: "human_screened",
      type: "singleSelect",
      access: {
        "agentic-framework": {
          mode: "read",
          filterFormula: "{human_screened} = 'complete'",
        },
      },
    },
    {
      name: "Sector",
      type: "multipleRecordLinks",
      access: {
        "airi-orgrev-orglist": { mode: "read" },
      },
    },
    {
      name: "Sector_Decomposed",
      type: "singleLineText",
      access: {
        "airi-orgrev-orglist": { mode: "read" },
      },
    },
    {
      name: "gvkey",
      type: "singleLineText",
      access: {
        "airi-orgrev-orglist": { mode: "read-write" },
      },
    },
    {
      name: "cmc_rank",
      type: "number",
      access: {
        "airi-orgrev-orglist": { mode: "read" },
      },
    },
    {
      name: "cmc_market_cap_numeric",
      type: "number",
      access: {
        "airi-orgrev-orglist": { mode: "read" },
      },
    },
    {
      name: "cmc_logo_url",
      type: "url",
      access: {
        "airi-orgrev-orglist": { mode: "read" },
        "airi-orgreview-logoprocessing": { mode: "read" },
      },
    },
    {
      name: "Logo",
      type: "multipleAttachments",
      access: {
        "airi-orgrev-orglist": {
          mode: "write",
          notes: "Attachment upload via upload_attachment()",
        },
        "airi-orgreview-logoprocessing": {
          mode: "read-write",
          notes:
            "Reads to check if Logo already exists; writes via upload_attachment()",
        },
      },
    },
    {
      name: "Included Documents",
      type: "multipleRecordLinks",
      access: {
        "airi-orgrev-orglist": { mode: "read" },
      },
    },
    {
      name: "fic",
      type: "singleLineText",
      access: {
        "airi-orgrev-orglist": { mode: "read-write" },
      },
    },
    {
      name: "gsector",
      type: "singleLineText",
      access: {
        "airi-orgrev-orglist": { mode: "read-write" },
      },
    },
    {
      name: "incorp",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "emp",
      type: "number",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "conml",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "loc",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "weburl",
      type: "url",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "busdesc",
      type: "multilineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "ggroup",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "gind",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "gsubind",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "naics",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "sic",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "costat",
      type: "singleSelect",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "cik",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
  ],
};
