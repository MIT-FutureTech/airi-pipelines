import { pipeline as examplePipeline } from "./example-pipeline/pipeline";
import { pipeline as documentProcessing } from "./document-processing/pipeline";

export const allPipelines = [documentProcessing, examplePipeline];
