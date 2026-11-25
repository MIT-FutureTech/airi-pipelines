export type Taxonomy = "Domain" | "Instrument" | "Practice";

export interface Code {
  record_id: string;
  key: string;
  taxonomy: Taxonomy;
  code: string | null;
  name: string;
  short_name: string | null;
  group: string | null;
  order: number;
  definition: string;
  details: string | null;
}

export interface Company {
  company_id: string;
  name: string;
  sector: string;
}

export type DatePrecision = "day" | "month" | "year";

export interface CompanyDocument {
  document_id: string;
  company_id: string;
  title: string;
  doc_type: string;
  date: string | null;
  date_precision: DatePrecision | null;
  link: string;
}

export interface Excerpt {
  excerpt_id: string;
  document_id: string;
  text: string;
  passage_ids: string[];
}

export interface Mitigation {
  record_id: string;
  mitigation_id: string;
  company_id: string;
  domain_record_id: string;
  instrument_record_id: string;
  practice_record_ids: string[];
  name: string;
  search_reasoning: string;
  instrument_reasoning: string;
  practice_tags: string | null;
  pipeline_run: string;
}

export type Strength = "described" | "stated" | "reference";

export interface Span {
  start: number;
  end: number;
}

export interface Quote {
  evidence_id: string;
  mitigation_record_id: string;
  document_id: string;
  excerpt_id: string;
  quote: string;
  strength: Strength;
  location: Span | null;
}

export interface Bundle {
  codes: Code[];
  companies: Company[];
  documents: CompanyDocument[];
  excerpts: Excerpt[];
  mitigations: Mitigation[];
  quotes: Quote[];
}
