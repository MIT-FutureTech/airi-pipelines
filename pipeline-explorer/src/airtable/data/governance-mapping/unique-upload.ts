import type { AirtableTable } from "@/airtable/types";

export const uniqueUpload: AirtableTable = {
  tableId: "tblZot2LtgZGxthp7",
  name: "Unique Upload",
  fields: [
    {
      name: "document_id",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Official name",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Authority",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Short summary",
      type: "multilineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "jurisdiction",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Link to document",
      type: "url",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Most recent activity",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Most recent activity date",
      type: "date",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "subdomain_*_*_coverage",
      type: "number",
      access: {
        "airi-navigator": {
          mode: "read",
          notes:
            "Multiple fields matching subdomain_X_Y_coverage pattern; values >= 2 indicate coverage",
        },
      },
    },
  ],
};
