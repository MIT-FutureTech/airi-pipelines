import type { AirtableTable } from "@/airtable/types";

export const llmPrompts: AirtableTable = {
  tableId: "tbljvaQKe4wjQvJiS",
  name: "llm_prompts",
  description:
    "Version history for LLM classification prompts used by airi-mitrev-classifier. Tracks prompt content, model, provider, reasoning effort, and changelog.",
  fields: [
    {
      name: "llm_version",
      type: "singleLineText",
      access: {
        "airi-mitrev-classifier": {
          mode: "read",
          filterFormula: "{llm_version} = '...'",
        },
      },
    },
    {
      name: "llm_prompt",
      type: "multilineText",
      access: { "airi-mitrev-classifier": { mode: "read" } },
    },
    {
      name: "is_active",
      type: "checkbox",
      access: {
        "airi-mitrev-classifier": {
          mode: "read",
          filterFormula: "{is_active} = TRUE()",
        },
      },
    },
    {
      name: "llm_model",
      type: "singleLineText",
      access: { "airi-mitrev-classifier": { mode: "read" } },
    },
    {
      name: "provider",
      type: "singleLineText",
      access: { "airi-mitrev-classifier": { mode: "read" } },
    },
    {
      name: "llm_effort",
      type: "singleSelect",
      access: { "airi-mitrev-classifier": { mode: "read" } },
    },
  ],
};
