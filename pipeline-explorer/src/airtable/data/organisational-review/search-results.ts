import type { AirtableTable } from "@/airtable/types";

export const searchResults: AirtableTable = {
  tableId: "tblb9eEVPpV4Qqo4u",
  name: "Search Results",
  alias: "raw_results",
  description:
    "All candidate documents from Google Search API and supplementary agent search. One row per retrieved URL. Stores LLM screening outputs and human review decisions side-by-side.",
  fields: [
    {
      name: "title",
      type: "singleLineText",
      access: {
        greylitsearcher: { mode: "write" },
        "airi-llm-screening-orchestrator": { mode: "read" },
        "agentic-framework": { mode: "read" },
        "org-doc-classifier": { mode: "read" },
      },
    },
    {
      name: "link",
      type: "url",
      access: {
        greylitsearcher: {
          mode: "write",
          notes: "Also used for duplicate checking via match({link})",
        },
        "airi-orgreview-fulltext": { mode: "read" },
        "airi-llm-screening-orchestrator": { mode: "read" },
        "agentic-framework": { mode: "read" },
        "org-doc-classifier": { mode: "read" },
      },
    },
    {
      name: "snippet",
      type: "multilineText",
      access: {
        greylitsearcher: { mode: "write" },
        "airi-llm-screening-orchestrator": { mode: "read" },
        "agentic-framework": { mode: "read" },
        "org-doc-classifier": { mode: "read" },
      },
    },
    {
      name: "source_domain",
      type: "singleLineText",
      access: {
        greylitsearcher: { mode: "write" },
        "org-doc-classifier": { mode: "read" },
      },
    },
    {
      name: "search_query",
      type: "singleLineText",
      access: {
        greylitsearcher: { mode: "write" },
      },
    },
    {
      name: "priority",
      type: "number",
      access: {
        greylitsearcher: { mode: "write" },
      },
    },
    {
      name: "scraped_at",
      type: "date",
      access: {
        greylitsearcher: { mode: "write" },
      },
    },
    {
      name: "status",
      type: "singleSelect",
      access: {
        greylitsearcher: { mode: "write", writtenAs: '"Todo"' },
        "airi-llm-screening-orchestrator": {
          mode: "read-write",
          filterFormula: "{status} = 'Todo'",
          writtenAs: '"Screened" (optional, if UPDATE_STATUS_FIELD=true)',
        },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "extraction_status",
      type: "singleSelect",
      access: {
        "airi-orgreview-fulltext": {
          mode: "read-write",
          filterFormula:
            "OR({extraction_status} = '', {extraction_status} = 'pending')",
          writtenAs: '"success", "error", "skipped"',
        },
      },
    },
    {
      name: "fulltext",
      type: "multilineText",
      access: {
        "airi-orgreview-fulltext": {
          mode: "write",
          notes:
            'Default field name is "fulltext" but configurable via FULLTEXT_FIELD env var. Other repos use "full_text".',
        },
      },
    },
    {
      name: "full_text",
      type: "multilineText",
      access: {
        "airi-llm-screening-orchestrator": { mode: "read-write" },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "full_text_extracted_at",
      type: "dateTime",
      access: {
        "airi-llm-screening-orchestrator": { mode: "write" },
      },
    },
    {
      name: "extraction_method",
      type: "singleLineText",
      access: {
        "airi-orgreview-fulltext": { mode: "write" },
      },
    },
    {
      name: "extraction_error",
      type: "multilineText",
      access: {
        "airi-orgreview-fulltext": { mode: "write" },
      },
    },
    {
      name: "content_length",
      type: "number",
      access: {
        "airi-orgreview-fulltext": { mode: "write" },
      },
    },
    {
      name: "content_type",
      type: "singleLineText",
      access: {
        "airi-orgreview-fulltext": { mode: "write" },
      },
    },
    {
      name: "include",
      type: "singleSelect",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "write",
          writtenAs: '"include" or "exclude"',
        },
        "agentic-framework": {
          mode: "read-write",
          writtenAs: '"include" or "exclude"',
        },
        "org-doc-classifier": {
          mode: "read",
          filterFormula: "AND({include}='include', {doc_type}=BLANK())",
        },
      },
    },
    {
      name: "confidence_level",
      type: "number",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "write",
          writtenAs: "0.00–1.00",
        },
        "agentic-framework": {
          mode: "read-write",
          writtenAs: "0.00–1.00",
        },
      },
    },
    {
      name: "short_reasoning",
      type: "singleLineText",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "write",
          writtenAs: "max 500 chars",
        },
        "agentic-framework": {
          mode: "read-write",
          writtenAs: "max 500 chars",
        },
      },
    },
    {
      name: "screening_status",
      type: "singleSelect",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "read-write",
          filterFormula:
            "OR({screening_status} = BLANK(), {screening_status} = '', NOT({screening_status} = 'screened'))",
          writtenAs: '"screened" or "error"',
        },
        "agentic-framework": {
          mode: "read-write",
          filterFormula: "{screening_status}='screened'",
          writtenAs: '"screened" or "error"',
        },
      },
    },
    {
      name: "screening_model_version",
      type: "singleLineText",
      access: {
        "airi-llm-screening-orchestrator": { mode: "write" },
        "agentic-framework": { mode: "write" },
      },
    },
    {
      name: "screening_prompt_version",
      type: "singleLineText",
      access: {
        "airi-llm-screening-orchestrator": { mode: "write" },
        "agentic-framework": { mode: "write" },
      },
    },
    {
      name: "screened_at",
      type: "dateTime",
      access: {
        "airi-llm-screening-orchestrator": { mode: "write" },
        "agentic-framework": { mode: "read-write" },
      },
    },
    {
      name: "text_source",
      type: "singleLineText",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "write",
          writtenAs: '"snippet" or "full_text"',
        },
      },
    },
    {
      name: "Organization (Link)",
      type: "multipleRecordLinks",
      access: {
        "airi-llm-screening-orchestrator": {
          mode: "read",
          notes: "Read as 'organization'",
        },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "Company Name",
      type: "multipleLookupValues",
      access: {
        "agentic-framework": { mode: "read" },
        "org-doc-classifier": { mode: "read" },
      },
    },
    {
      name: "Domain",
      type: "multipleRecordLinks",
      access: {
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "doc_type",
      type: "singleSelect",
      access: {
        "org-doc-classifier": {
          mode: "write",
          notes: "Auto-created via Metadata API if missing",
        },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "doc_type_conf",
      type: "number",
      access: {
        "org-doc-classifier": {
          mode: "write",
          writtenAs: "0.00–1.00",
          notes: "Auto-created via Metadata API if missing",
        },
        "agentic-framework": { mode: "read" },
      },
    },
    {
      name: "doc_type_reason",
      type: "multilineText",
      access: {
        "org-doc-classifier": {
          mode: "write",
          notes: "Auto-created via Metadata API if missing",
        },
        "agentic-framework": { mode: "read" },
      },
    },
    // --- Human review fields (not touched by code) ---
    {
      name: "human_review",
      type: "singleSelect",
      access: {
        "agentic-framework": {
          mode: "read",
          filterFormula: "{human_review}!=''",
        },
      },
    },
    {
      name: "human_reasoning",
      type: "multilineText",
      access: {
        "agentic-framework": { mode: "read" },
      },
    },
  ],
};
