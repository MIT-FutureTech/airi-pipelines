import { Alert, AppShell, Loader, Stack, Title } from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { Suspense, use, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { EvidenceGrid } from "@/components/EvidenceGrid";
import { EvidencePanel } from "@/components/EvidencePanel";
import { StrengthLegend } from "@/components/StrengthLegend";
import { getBundle } from "@/lib/api";
import { type CellSelection, cellKey, evidenceByCell } from "@/lib/cells";

export function App() {
  return (
    <ErrorBoundary fallbackRender={renderError}>
      <Suspense fallback={<Loader m="xl" />}>
        <Reviewer />
      </Suspense>
    </ErrorBoundary>
  );
}

function Reviewer() {
  const bundle = use(getBundle());
  const cells = evidenceByCell(bundle.evidence, bundle.documents);
  const documents = new Map(
    bundle.documents.map((document) => [document.document_id, document]),
  );
  const [selection, setSelection] = useState<CellSelection | null>(null);
  useHotkeys([["Escape", () => setSelection(null)]]);

  const isPanelClosed = selection === null;
  return (
    <AppShell
      padding="md"
      aside={{
        width: 560,
        breakpoint: "sm",
        collapsed: { desktop: isPanelClosed, mobile: isPanelClosed },
      }}
    >
      <AppShell.Main>
        <Stack>
          <Title order={2}>Organization Mitigations Reviewer</Title>
          <StrengthLegend />
          <EvidenceGrid
            companies={bundle.companies}
            taxonomy={bundle.taxonomy}
            cells={cells}
            selection={selection}
            onSelect={setSelection}
          />
        </Stack>
      </AppShell.Main>
      <AppShell.Aside p="md">
        {selection !== null && (
          <EvidencePanel
            key={cellKey(selection.company.company_id, selection.code.code)}
            selection={selection}
            documents={documents}
            onClose={() => setSelection(null)}
          />
        )}
      </AppShell.Aside>
    </AppShell>
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Alert m="xl" color="red" title="Couldn't load data">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
