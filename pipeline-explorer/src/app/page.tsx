import { PipelineView } from "@/pipeline/components/PipelineView";
import { allPipelines, allSharedNodes } from "@/pipeline/data";

export default function Home() {
  return <PipelineView pipelines={allPipelines} sharedNodes={allSharedNodes} />;
}
