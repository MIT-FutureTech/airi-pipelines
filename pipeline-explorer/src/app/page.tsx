import { allPipelines, allSharedNodes } from "@/pipeline/data";
import { ClientShell } from "@/shared/components/ClientShell";

export default function Home() {
  return <ClientShell pipelines={allPipelines} sharedNodes={allSharedNodes} />;
}
