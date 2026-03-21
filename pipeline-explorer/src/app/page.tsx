import { ClientShell } from "@/components/ClientShell";
import { allPipelines, allSharedNodes } from "@/pipelines";

export default function Home() {
  return <ClientShell pipelines={allPipelines} sharedNodes={allSharedNodes} />;
}
