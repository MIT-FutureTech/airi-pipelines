import { Alert, Container, Loader, Stack, Title } from "@mantine/core";
import { Suspense, use } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { EvidenceGrid } from "@/components/EvidenceGrid";
import { StrengthLegend } from "@/components/StrengthLegend";
import { getBundle } from "@/lib/api";
import { evidenceByCell } from "@/lib/cells";

export function App() {
  return (
    <Container fluid py="xl">
      <Stack>
        <Title order={2}>Organization Mitigations Reviewer</Title>
        <ErrorBoundary fallbackRender={renderError}>
          <Suspense fallback={<Loader />}>
            <Reviewer />
          </Suspense>
        </ErrorBoundary>
      </Stack>
    </Container>
  );
}

function Reviewer() {
  const bundle = use(getBundle());
  const cells = evidenceByCell(bundle.evidence, bundle.documents);
  return (
    <>
      <StrengthLegend />
      <EvidenceGrid
        companies={bundle.companies}
        taxonomy={bundle.taxonomy}
        cells={cells}
      />
    </>
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Alert color="red" title="Couldn't load data">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
