import {
  Alert,
  AppShell,
  Loader,
  SegmentedControl,
  Stack,
  Title,
} from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { Suspense, use, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { EvidenceGrid } from "@/components/EvidenceGrid";
import { EvidencePanel } from "@/components/EvidencePanel";
import { MockupNotice } from "@/components/MockupNotice";
import { StrengthLegend } from "@/components/StrengthLegend";
import { getBundle, getJudgements } from "@/lib/api";
import {
  type CellSelection,
  cellKey,
  mitigationsByCell,
  quotesByMitigation,
} from "@/lib/cells";
import {
  codeGroups,
  parseTaxonomy,
  TAXONOMIES,
  TAXONOMY_LABELS,
} from "@/lib/codes";
import { emptyJudgement, judgementsByCell } from "@/lib/judgements";
import type { Taxonomy } from "@/lib/types";

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
  const bundleRequest = getBundle();
  const judgementsRequest = getJudgements();
  const bundle = use(bundleRequest);
  const saved = use(judgementsRequest);
  const [taxonomy, setTaxonomy] = useState<Taxonomy>("Domain");
  const cells = mitigationsByCell(bundle.mitigations, taxonomy);
  const quotes = quotesByMitigation(bundle.quotes);
  const groups = codeGroups(bundle.codes, taxonomy);
  const documents = new Map(
    bundle.documents.map((document) => [document.document_id, document]),
  );
  const excerpts = new Map(
    bundle.excerpts.map((excerpt) => [excerpt.excerpt_id, excerpt]),
  );
  const [selection, setSelection] = useState<CellSelection | null>(null);
  const [judgements, setJudgements] = useState(() =>
    judgementsByCell(saved.judgements),
  );
  useHotkeys([["Escape", () => setSelection(null)]]);

  const selectedKey =
    selection &&
    cellKey(selection.company.company_id, selection.code.record_id);
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
          <MockupNotice companyCount={bundle.companies.length} />
          <StrengthLegend />
          <SegmentedControl
            aria-label="Taxonomy"
            data={TAXONOMIES.map((value) => ({
              value,
              label: TAXONOMY_LABELS[value],
            }))}
            value={taxonomy}
            onChange={(value) => {
              setTaxonomy(parseTaxonomy(value));
              setSelection(null);
            }}
          />
          <EvidenceGrid
            companies={bundle.companies}
            groups={groups}
            cells={cells}
            quotes={quotes}
            judgements={judgements}
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
            quotes={quotes}
            documents={documents}
            excerpts={excerpts}
            judgement={
              judgements.get(selectedKey) ??
              emptyJudgement(
                selection.company.company_id,
                selection.code.record_id,
              )
            }
            onJudgementChange={(judgement) =>
              setJudgements((current) =>
                new Map(current).set(selectedKey, judgement),
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
