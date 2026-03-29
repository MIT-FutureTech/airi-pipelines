import type { AirtableTable } from "@/airtable/types";

export const sysRevMitigationDatabase: AirtableTable = {
  tableId: "tblZRKlssxugpZAfr",
  name: "SysRev_MitigationDatabase",
  fields: [
    {
      name: "Mitigation_Name",
      type: "singleLineText",
      access: {
        "airi-mitrev-classifier": { mode: "read" },
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "Definition",
      type: "multilineText",
      access: {
        "airi-mitrev-classifier": { mode: "read" },
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "Additional Information",
      type: "richText",
      access: {
        "airi-mitrev-classifier": { mode: "read" },
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "Source",
      type: "multipleRecordLinks",
      access: {
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "Parent",
      type: "multipleRecordLinks",
      access: {
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "Children",
      type: "multipleRecordLinks",
      access: {
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "Status",
      type: "singleSelect",
      access: {
        "airi-mitrev-classifier": {
          mode: "read-write",
          filterFormula: "{Status} = 'llm_todo'",
          writtenAs: '"llm_classified"',
        },
      },
    },
    {
      name: "llm_classification",
      type: "singleLineText",
      access: {
        "airi-mitrev-classifier": { mode: "write" },
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "llm_reasoning",
      type: "multilineText",
      access: {
        "airi-mitrev-classifier": {
          mode: "write",
          writtenAs: "max 500 chars",
        },
      },
    },
    {
      name: "llm_version",
      type: "singleLineText",
      access: {
        "airi-mitrev-classifier": { mode: "write" },
      },
    },
    {
      name: "llm_datetime",
      type: "dateTime",
      access: {
        "airi-mitrev-classifier": { mode: "write" },
      },
    },
    {
      name: "human_classification",
      type: "multipleRecordLinks",
      access: {
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "MitTax_Name",
      type: "multipleLookupValues",
      access: {
        "airi-navigator": { mode: "read" },
      },
    },
    {
      name: "AILifecycle_Primary",
      type: "singleSelect",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "AILifecycle_Other",
      type: "multipleSelects",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "AIActor_Primary",
      type: "singleSelect",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "AIActor_Other",
      type: "multipleSelects",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "AIRM_Primary",
      type: "singleSelect",
      access: { "airi-navigator": { mode: "read" } },
    },
    {
      name: "AIRM_Other",
      type: "multipleSelects",
      access: { "airi-navigator": { mode: "read" } },
    },
  ],
};
