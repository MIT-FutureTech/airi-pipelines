import { Alert, Center, Loader } from "@mantine/core";
import { Suspense, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { ClassificationReview } from "@/components/ClassificationReview";
import { NamePrompt } from "@/components/NamePrompt";
import { TaskLauncher } from "@/components/TaskLauncher";
import { Validator } from "@/components/Validator";
import { clearReviewer, loadReviewer, saveReviewer } from "@/lib/storage";
import type { TaskSelection } from "@/lib/task";

export function App() {
  const [reviewer, setReviewer] = useState<string | null>(loadReviewer);
  const [selection, setSelection] = useState<TaskSelection | null>(null);

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

  if (selection === null) {
    return (
      <TaskLauncher
        reviewer={reviewer}
        onSelect={setSelection}
        onChangeName={() => {
          clearReviewer();
          setReviewer(null);
          setSelection(null);
        }}
      />
    );
  }

  const selectionKey =
    selection.task === "screening"
      ? "screening"
      : `classification:${selection.extractionRun}:${selection.mode}`;

  return (
    <ErrorBoundary
      fallbackRender={renderError}
      resetKeys={[reviewer, selectionKey]}
    >
      <Suspense
        fallback={
          <Center h="100vh">
            <Loader />
          </Center>
        }
      >
        {selection.task === "screening" ? (
          <Validator reviewer={reviewer} />
        ) : (
          <ClassificationReview
            reviewer={reviewer}
            selection={selection}
            onExit={() => setSelection(null)}
          />
        )}
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
