import { Alert, Container, Loader, Stack, Title } from "@mantine/core";
import { Suspense, use } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { EvidenceGrid } from "@/components/EvidenceGrid";
import { getBundle } from "@/lib/api";

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
  return (
    <EvidenceGrid companies={bundle.companies} taxonomy={bundle.taxonomy} />
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Alert color="red" title="Couldn't load data">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
