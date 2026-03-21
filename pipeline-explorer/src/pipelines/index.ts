import { pipeline as documentProcessing } from "./document-processing/pipeline";
import { pipeline as actors } from "./actors/pipeline";

export const allPipelines = [
  documentProcessing,
  actors,
];
