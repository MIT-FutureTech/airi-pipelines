import {
  Alert,
  AppShell,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { Suspense, use } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { BundlePicker } from "@/components/BundlePicker";
import { getBundle } from "@/lib/api";
import { useUrlParam } from "@/lib/useUrlParam";

export function App() {
  const [bundleFilename, setBundleFilename] = useUrlParam("bundle");

  return (
    <AppShell
      header={{ height: 64 }}
      navbar={{ width: 320, breakpoint: "sm" }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" gap="md">
          <Title order={4}>Risk Repository Auditor</Title>
          <ErrorBoundary fallbackRender={renderInlineError}>
            <Suspense
              fallback={
                <Text c="dimmed" size="sm">
                  Loading bundles…
                </Text>
              }
            >
              <BundlePicker
                value={bundleFilename}
                onChange={setBundleFilename}
              />
            </Suspense>
          </ErrorBoundary>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <Text c="dimmed" size="sm">
          Document list will go here
        </Text>
      </AppShell.Navbar>
      <AppShell.Main>
        {bundleFilename === null ? (
          <Text c="dimmed">Select a bundle to begin.</Text>
        ) : (
          <ErrorBoundary
            fallbackRender={renderBlockError}
            resetKeys={[bundleFilename]}
          >
            <Suspense fallback={<Loader />}>
              <BundleContent filename={bundleFilename} />
            </Suspense>
          </ErrorBoundary>
        )}
      </AppShell.Main>
    </AppShell>
  );
}

function BundleContent({ filename }: { filename: string }) {
  const bundle = use(getBundle(filename));
  return (
    <Stack gap="xs">
      <Text>
        {bundle.run_name ?? bundle.results_dir}: {bundle.documents.length}{" "}
        documents
      </Text>
      <Text c="dimmed" size="sm">
        Bundle generated at {bundle.generated_at}
      </Text>
    </Stack>
  );
}

function renderInlineError({ error }: FallbackProps) {
  return (
    <Text c="red" size="sm">
      {error instanceof Error ? error.message : String(error)}
    </Text>
  );
}

function renderBlockError({ error }: FallbackProps) {
  return (
    <Alert color="red" title="Error">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
