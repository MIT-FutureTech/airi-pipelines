import type { AirtableTable } from "@/airtable/types";

export const sysRevDocuments: AirtableTable = {
  tableId: "tbleVxrlfEZvuFBJI",
  name: "SysRev_Documents",
  description:
    "Source documents for the mitigation systematic review. One row per paper. Title, authors, year, URL, DOI, abstract.",
  fields: [
    {
      name: "SourceID",
      type: "formula",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Title",
      type: "multilineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "First author",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Author list",
      type: "multilineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Year",
      type: "number",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "URL",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "DOI",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Abstract",
      type: "multilineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Description",
      type: "multilineText",
      access: { "airi-navigator": { mode: "read" } },
    },
  ],
};
