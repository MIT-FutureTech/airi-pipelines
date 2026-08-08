import type { ReviewMode } from "@api/_classification";

export interface ClassificationSelection {
  task: "classification";
  quickRef: string;
  mode: ReviewMode;
}

export type TaskSelection = { task: "screening" } | ClassificationSelection;
