import type { AirtableTable } from "@/airtable/types";

export const screeningPrompts: AirtableTable = {
  tableId: "tblwVxxrSAAdK5R9n",
  name: "screening_prompts",
  description:
    "Version history for LLM screening prompts. Tracks prompt content, model, provider, active status, and changelog.",
  fields: [
    {
      name: "version",
      type: "singleLineText",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "read",
          filterFormula: "{version} = '...'",
        },
        "agentic-framework": {
          mode: "read",
          filterFormula: "{version} = '...'",
        },
      },
    },
    {
      name: "prompt_content",
      type: "multilineText",
      access: {
        "airi-llm-screening-orchestrator": { mode: "read" },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "is_active",
      type: "checkbox",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "read",
          filterFormula: "{is_active} = TRUE()",
        },
        "agentic-framework": {
          mode: "read",
          filterFormula: "{is_active} = TRUE()",
        },
      },
    },
    {
      name: "model",
      type: "singleLineText",
      access: {
        "airi-llm-screening-orchestrator": { mode: "read" },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "provider",
      type: "singleSelect",
      access: {
        "airi-llm-screening-orchestrator": { mode: "read" },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "use_full_text",
      type: "checkbox",
      access: {
        "airi-llm-screening-orchestrator": { mode: "read" },
      },
    },
  ],
};
