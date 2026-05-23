import { Alert, Center, Loader } from "@mantine/core";
import { Suspense, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { NamePrompt } from "@/components/NamePrompt";
import { Validator } from "@/components/Validator";
import { loadReviewer, saveReviewer } from "@/lib/storage";

export function App() {
  const [reviewer, setReviewer] = useState<string | null>(loadReviewer);

  if (reviewer === null) {
    return (
      <NamePrompt
        onSubmit={(name) => {
          saveReviewer(name);
          setReviewer(name);
        }}
      />
    );
  }

  return (
    <ErrorBoundary fallbackRender={renderError} resetKeys={[reviewer]}>
      <Suspense
        fallback={
          <Center h="100vh">
            <Loader />
          </Center>
        }
      >
        <Validator reviewer={reviewer} />
      </Suspense>
    </ErrorBoundary>
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Center h="100vh" p="md">
      <Alert color="red" title="Error" maw={600}>
        {error instanceof Error ? error.message : String(error)}
      </Alert>
    </Center>
  );
}
