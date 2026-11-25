import {
  Alert,
  AppShell,
  Group,
  Loader,
  SegmentedControl,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useHotkeys } from "@mantine/hooks";
import { Suspense, use, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { EvidenceGrid } from "@/components/EvidenceGrid";
import { EvidencePanel } from "@/components/EvidencePanel";
import { ShortcutsHelp } from "@/components/ShortcutsHelp";
import { StrengthLegend } from "@/components/StrengthLegend";
import { getBundle, getJudgements } from "@/lib/api";
import {
  type CellSelection,
  cellKey,
  type Direction,
  mitigationsByCell,
  nextCodeWithMitigations,
  quotesByMitigation,
} from "@/lib/cells";
import {
  codeGroups,
  parseTaxonomy,
  TAXONOMIES,
  TAXONOMY_LABELS,
} from "@/lib/codes";
import { emptyJudgement } from "@/lib/judgements";
import type { Code, Taxonomy } from "@/lib/types";
import { useJudgements } from "@/lib/useJudgements";

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
  const { judgements, saveStatuses, change, save } = useJudgements(
    saved.judgements,
  );
  useHotkeys([["Escape", () => setSelection(null)]], ["TEXTAREA"]);

  const codes = groups.flatMap((group) => group.codes);
  const neighbour = (direction: Direction) =>
    selection &&
    nextCodeWithMitigations(
      codes,
      cells,
      selection.company.company_id,
      selection.code.record_id,
      direction,
    );
  const selectCode = (code: Code) => {
    if (selection === null) {
      return;
    }
    const mitigations = cells.get(
      cellKey(selection.company.company_id, code.record_id),
    );
    if (mitigations === undefined) {
      throw new Error(
        `${selection.company.name} has no ${code.key} mitigations`,
      );
    }
    setSelection({ company: selection.company, code, mitigations });
  };

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
          <Group gap="md" wrap="nowrap">
            <Title order={2}>Organization Mitigations Reviewer</Title>
            <ShortcutsHelp />
          </Group>
          <Text>
            Click a shaded cell to see the mitigations and quotes behind it,
            then record your judgement.
          </Text>
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
            saveStatus={saveStatuses.get(selectedKey) ?? null}
            previousCode={neighbour("previous")}
            nextCode={neighbour("next")}
            onSelectCode={selectCode}
            onJudgementChange={change}
            onJudgementSave={(judgement) =>
              save(judgement, selection.company.name, selection.code.key)
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
