import type { AirtableTable } from "@/airtable/types";

export const organizationActorRole: AirtableTable = {
  tableId: "tblyO155su2M9nCLW",
  name: "Organization Actor Role",
  description:
    "LLM-generated and human-validated actor role classification. One row per organisation. Primary role, secondary roles, per-role evidence and counter-evidence.",
  fields: [
    {
      name: "cmc_rank (from cmc_company_name)",
      type: "multipleLookupValues",
      access: {
        "ai-actor-classifier": {
          mode: "read",
          notes: "Used for record matching (rank → record ID)",
        },
      },
    },
    {
      name: "Company Name",
      type: "singleLineText",
      access: {
        "ai-actor-classifier": { mode: "write" },
      },
    },
    {
      name: "Date Classified",
      type: "date",
      access: {
        "ai-actor-classifier": { mode: "write" },
      },
    },
    {
      name: "Primary AI Role",
      type: "singleSelect",
      access: {
        "ai-actor-classifier": { mode: "write" },
      },
    },
    {
      name: "Secondary AI Roles",
      type: "multipleSelects",
      access: {
        "ai-actor-classifier": { mode: "write" },
      },
    },
    {
      name: "Model Reflection",
      type: "multilineText",
      access: {
        "ai-actor-classifier": { mode: "write" },
      },
    },
    {
      name: "AI Developer (General) [EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Developer (General) [COUNTER-EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Developer (General) - AI Reflection",
      type: "multilineText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Developer (Specialized) [EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Developer (Specialized) [COUNTER-EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Developer (Specialized) - AI Reflection",
      type: "multilineText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Deployer [EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Deployer [COUNTER-EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Deployer - AI Reflection",
      type: "multilineText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Infrastructure Provider [EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Infrastructure Provider [COUNTER-EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Infrastructure Provider - AI Reflection",
      type: "multilineText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Governance Actor [EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Governance Actor [COUNTER-EVIDENCE]",
      type: "richText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
    {
      name: "AI Governance Actor - AI Reflection",
      type: "multilineText",
      access: { "ai-actor-classifier": { mode: "write" } },
    },
  ],
};
