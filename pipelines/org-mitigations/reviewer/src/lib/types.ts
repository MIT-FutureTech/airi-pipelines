// biome-ignore-all lint/style/useNamingConvention: these fields must match what Python outputs
export interface RunSettings {
  prompt_file: string;
  model: string;
  temperature: number;
  reasoning_effort: string;
}

export interface Domain {
  code: string;
  name: string;
  short_name: string;
  definition: string;
  examples: string[];
}

export interface Locus {
  code: string;
  name: string;
  short_name: string;
  definition: string;
  domains: Domain[];
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

export type Strength = "described" | "stated" | "reference";

export interface Span {
  start: number;
  end: number;
}

export interface LocatedEvidence {
  document_id: string;
  code: string;
  mitigation: string;
  quote: string;
  strength: Strength;
  excerpt_id: string;
  location: Span | null;
}

export interface Bundle {
  run: RunSettings;
  taxonomy: Locus[];
  companies: Company[];
  documents: CompanyDocument[];
  excerpts: Excerpt[];
  evidence: LocatedEvidence[];
}
