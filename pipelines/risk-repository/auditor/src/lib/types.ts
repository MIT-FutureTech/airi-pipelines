// biome-ignore-all lint/style/useNamingConvention: these fields must match what Python outputs
export type Decision = "include" | "exclude" | "uncertain";

export type OutcomeClass =
  | "true_positive"
  | "false_positive"
  | "true_negative"
  | "false_negative"
  | "unlabeled";

export interface ScreeningResult {
  criteria_breakdown: string;
  decision: Decision;
}

export interface ScreeningAudit {
  ground_truth_decision: Decision | null;
  abstract_result: ScreeningResult | null;
  full_text_result: ScreeningResult | null;
  outcome_class: OutcomeClass;
}

export interface AuditDocument {
  readable_id: string;
  title: string | null;
  url: string | null;
  pdf_path: string | null;
  abstract: string | null;
  screening: ScreeningAudit;
}

export interface AuditBundle {
  run_name: string | null;
  results_dir: string;
  generated_at: string;
  documents: AuditDocument[];
}

export interface ManifestEntry {
  filename: string;
  run_name: string | null;
  generated_at: string;
}

export interface Manifest {
  bundles: ManifestEntry[];
}
