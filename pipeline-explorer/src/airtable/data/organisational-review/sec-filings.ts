import type { AirtableTable } from "@/airtable/types";

export const secFilings: AirtableTable = {
  tableId: "tblE0lKFB66dLjv7i",
  name: "SEC Filings",
  fields: [
    {
      name: "cik",
      type: "multipleLookupValues",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "accession",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "company_name",
      type: "multipleLookupValues",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "filing_type",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "fyear",
      type: "number",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "filing_date",
      type: "date",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "doc_status",
      type: "singleSelect",
      access: {
        "airi-orgrev-orglist": {
          mode: "read-write",
          writtenAs: '"Downloaded", "Extracted"',
        },
      },
    },
    {
      name: "doc_file",
      type: "multipleAttachments",
      access: {
        "airi-orgrev-orglist": {
          mode: "write",
          notes: "HTM/HTML filing attachment",
        },
      },
    },
    {
      name: "doc_wordcount",
      type: "number",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "doc_risktext",
      type: "multilineText",
      access: {
        "airi-orgrev-orglist": {
          mode: "write",
          notes: "Extracted Item 1A (10-K) or Item 3.D (20-F)",
        },
      },
    },
    {
      name: "doc_riskwordcount",
      type: "number",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
  ],
};
