import type { AirtableTable } from "@/airtable/types";

export const includedDocuments: AirtableTable = {
  tableId: "tblppga8ctRLam672",
  name: "Included Documents",
  description:
    "Document corpus including screening status. One row per included document. PDF attachment, document type, annual report sub-type.",
  fields: [
    {
      name: "Document ID",
      type: "singleLineText",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "DocStatus",
      type: "singleSelect",
      access: {
        "airi-orgrev-orglist": {
          mode: "read",
          filterFormula: "{DocStatus} = 'Validated'",
        },
      },
    },
    {
      name: "Title",
      type: "multipleRecordLinks",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "doc_type",
      type: "singleSelect",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "link",
      type: "multipleLookupValues",
      access: { "airi-orgrev-orglist": { mode: "read" } },
    },
    {
      name: "DocFile",
      type: "multipleAttachments",
      access: {
        "airi-orgrev-orglist": {
          mode: "read",
          notes: "PDF attachments downloaded for analysis",
        },
      },
    },
    {
      name: "analysis_status",
      type: "singleSelect",
      access: {
        "airi-orgrev-orglist": {
          mode: "read-write",
          filterFormula: "{analysis_status} != 'Completed'",
          writtenAs: '"Completed"',
        },
      },
    },
    {
      name: "mention_count",
      type: "number",
      access: { "airi-orgrev-orglist": { mode: "write" } },
    },
    {
      name: "keywords_found",
      type: "singleLineText",
      access: {
        "airi-orgrev-orglist": {
          mode: "write",
          notes: "Pipe-separated list of keywords",
        },
      },
    },
  ],
};
