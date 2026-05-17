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
import { DocumentDetail } from "@/components/DocumentDetail";
import { DocumentList } from "@/components/DocumentList";
import { getBundle } from "@/lib/api";
import { useUrlParam } from "@/lib/useUrlParam";

export function App() {
  const [bundleFilename, setBundleFilename] = useUrlParam("bundle");
  const [selectedId, setSelectedId] = useUrlParam("id");

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
                onChange={(value) => {
                  setBundleFilename(value);
                  setSelectedId(null);
                }}
              />
            </Suspense>
          </ErrorBoundary>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        {bundleFilename === null ? (
          <Text c="dimmed" size="sm">
            Select a bundle.
          </Text>
        ) : (
          <ErrorBoundary
            fallbackRender={renderBlockError}
            resetKeys={[bundleFilename]}
          >
            <Suspense fallback={<Loader />}>
              <NavbarContent
                filename={bundleFilename}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </Suspense>
          </ErrorBoundary>
        )}
      </AppShell.Navbar>
      <AppShell.Main>
        {bundleFilename === null ? (
          <Text c="dimmed">Select a bundle to begin.</Text>
        ) : (
          <ErrorBoundary
            fallbackRender={renderBlockError}
            resetKeys={[bundleFilename, selectedId]}
          >
            <Suspense fallback={<Loader />}>
              <MainContent filename={bundleFilename} selectedId={selectedId} />
            </Suspense>
          </ErrorBoundary>
        )}
      </AppShell.Main>
    </AppShell>
  );
}

interface NavbarContentProps {
  filename: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function NavbarContent({ filename, selectedId, onSelect }: NavbarContentProps) {
  const bundle = use(getBundle(filename));
  return (
    <DocumentList bundle={bundle} selectedId={selectedId} onSelect={onSelect} />
  );
}

interface MainContentProps {
  filename: string;
  selectedId: string | null;
}

function MainContent({ filename, selectedId }: MainContentProps) {
  const bundle = use(getBundle(filename));
  if (selectedId === null) {
    return (
      <Stack gap="xs">
        <Text>
          {bundle.run_name ?? bundle.results_dir}: {bundle.documents.length}{" "}
          documents
        </Text>
        <Text c="dimmed">Select a document from the sidebar.</Text>
      </Stack>
    );
  }
  const document = bundle.documents.find((d) => d.readable_id === selectedId);
  if (document === undefined) {
    return (
      <Text c="dimmed">Document "{selectedId}" is not in this bundle.</Text>
    );
  }
  return <DocumentDetail document={document} />;
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
