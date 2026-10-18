import { Alert, Container, Loader, Stack, Text, Title } from "@mantine/core";
import { Suspense, use } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { getBundle } from "@/lib/api";

export function App() {
  return (
    <Container py="xl">
      <Stack>
        <Title order={2}>Organization Mitigations Reviewer</Title>
        <ErrorBoundary fallbackRender={renderError}>
          <Suspense fallback={<Loader />}>
            <BundleSummary />
          </Suspense>
        </ErrorBoundary>
      </Stack>
    </Container>
  );
}

function BundleSummary() {
  const bundle = use(getBundle());
  return (
    <Text>
      {bundle.companies.length} companies, {bundle.documents.length} documents,{" "}
      {bundle.evidence.length} quotes
    </Text>
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Alert color="red" title="Couldn't load data">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
