import { Alert, AppShell, Loader, Stack, Title } from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { Suspense, use, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { EvidenceGrid } from "@/components/EvidenceGrid";
import { EvidencePanel } from "@/components/EvidencePanel";
import { MockupNotice } from "@/components/MockupNotice";
import { StrengthLegend } from "@/components/StrengthLegend";
import { getBundle } from "@/lib/api";
import { type CellSelection, cellKey, evidenceByCell } from "@/lib/cells";
import { type Decision, NO_DECISION } from "@/lib/decisions";

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
  const excerpts = new Map(
    bundle.excerpts.map((excerpt) => [excerpt.excerpt_id, excerpt]),
  );
  const [selection, setSelection] = useState<CellSelection | null>(null);
  const [decisions, setDecisions] = useState(() => new Map<string, Decision>());
  useHotkeys([["Escape", () => setSelection(null)]]);

  const selectedKey =
    selection && cellKey(selection.company.company_id, selection.domain.code);
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
          <MockupNotice
            run={bundle.run}
            companyCount={bundle.companies.length}
            codeCount={bundle.taxonomy.flatMap((locus) => locus.domains).length}
          />
          <StrengthLegend />
          <EvidenceGrid
            companies={bundle.companies}
            taxonomy={bundle.taxonomy}
            cells={cells}
            decisions={decisions}
            selection={selection}
            onSelect={setSelection}
          />
        </Stack>
      </AppShell.Main>
      <AppShell.Aside p="md">
        {selection !== null && selectedKey !== null && (
          <EvidencePanel
            key={selectedKey}
            selection={selection}
            documents={documents}
            excerpts={excerpts}
            decision={decisions.get(selectedKey) ?? NO_DECISION}
            onDecisionChange={(decision) =>
              setDecisions((current) =>
                new Map(current).set(selectedKey, decision),
              )
            }
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
