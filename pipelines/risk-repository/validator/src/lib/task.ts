import type { ReviewMode } from "@api/_classification";

export interface ClassificationSelection {
  task: "classification";
  extractionRun: string;
  mode: ReviewMode;
  pipelineReviewer: string | null;
}

export type TaskSelection = { task: "screening" } | ClassificationSelection;
