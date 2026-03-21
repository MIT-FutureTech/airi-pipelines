import { allPipelines, allSharedNodes } from "@/pipelines";
import { ClientShell } from "@/components/ClientShell";

export default function Home() {
  return <ClientShell pipelines={allPipelines} sharedNodes={allSharedNodes} />;
}
