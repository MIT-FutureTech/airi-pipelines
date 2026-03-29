import type { AirtableTable } from "@/airtable/types";

export const classifications: AirtableTable = {
  tableId: "tblA8dZPux36bV6ox",
  name: "Classifications",
  fields: [
    {
      name: "Title",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Description",
      type: "multilineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Date",
      type: "date",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Subdomain",
      type: "singleLineText",
      access: {
        "airi-navigator": {
          mode: "read",
          notes: "Parsed as X.Y format to derive subdomainId",
        },
      },
    },
    {
      name: "Entity",
      type: "singleSelect",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Intent",
      type: "singleSelect",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Timing",
      type: "singleSelect",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Alleged deployer",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Alleged developer",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "Alleged harmed parties",
      type: "singleLineText",
      access: { "airi-navigator": { mode: "read" } },
    },
  ],
};
