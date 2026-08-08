import { Alert, Button, Center, Loader, Stack } from "@mantine/core";
import { Suspense, useState } from "react";
import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { ClassificationReview } from "@/components/ClassificationReview";
import { NamePrompt } from "@/components/NamePrompt";
import { PaperPicker } from "@/components/PaperPicker";
import { TaskLauncher } from "@/components/TaskLauncher";
import { Validator } from "@/components/Validator";
import { navigate, type Route, routeKey, useRoute } from "@/lib/route";
import { clearReviewer, loadReviewer, saveReviewer } from "@/lib/storage";

export function App() {
  const [reviewer, setReviewer] = useState<string | null>(loadReviewer);
  const route = useRoute();

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

  const onChangeName = () => {
    clearReviewer();
    setReviewer(null);
    navigate({ name: "tasks" });
  };

  if (route.name === "tasks") {
    return <TaskLauncher reviewer={reviewer} onChangeName={onChangeName} />;
  }

  return (
    <Screen resetKey={`${reviewer}:${routeKey(route)}`}>
      <Content reviewer={reviewer} route={route} />
    </Screen>
  );
}

function Content({ reviewer, route }: { reviewer: string; route: Route }) {
  switch (route.name) {
    case "screening":
      return <Validator reviewer={reviewer} />;
    case "papers":
      return <PaperPicker reviewer={reviewer} />;
    case "classification":
      return (
        <ClassificationReview
          reviewer={reviewer}
          quickRef={route.quickRef}
          mode={route.mode}
        />
      );
    case "tasks":
      return null;
  }
}

interface ScreenProps {
  resetKey: string;
  children: React.ReactNode;
}

function Screen({ resetKey, children }: ScreenProps) {
  return (
    <ErrorBoundary fallbackRender={renderError} resetKeys={[resetKey]}>
      <Suspense
        fallback={
          <Center h="100vh">
            <Loader />
          </Center>
        }
      >
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}

function renderError({ error }: FallbackProps) {
  return (
    <Center h="100vh" p="md">
      <Stack gap="md" maw={600}>
        <Alert color="red" title="Error">
          {error instanceof Error ? error.message : String(error)}
        </Alert>
        <Button
          variant="default"
          onClick={() => navigate({ name: "tasks" })}
          style={{ alignSelf: "flex-start" }}
        >
          Back to tasks
        </Button>
      </Stack>
    </Center>
  );
}
