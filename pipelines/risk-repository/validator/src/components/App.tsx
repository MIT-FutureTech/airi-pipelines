import { Center, Loader } from "@mantine/core";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { ClassificationReview } from "@/components/ClassificationReview";
import { ErrorScreen } from "@/components/ErrorScreen";
import { Home } from "@/components/Home";
import { PaperPicker } from "@/components/PaperPicker";
import { Validator } from "@/components/Validator";
import { type Route, routeKey, useRoute } from "@/lib/route";
import { airtableSource } from "@/lib/source";
import { loadReviewer, saveReviewer } from "@/lib/storage";
import { TourScreen } from "@/tour/TourScreen";

export function App() {
  const [reviewer, setReviewer] = useState<string | null>(loadReviewer);
  const route = useRoute();

  if (reviewer === null || route.name === "tasks") {
    return (
      <Home
        reviewer={reviewer}
        resuming={route.name !== "tasks"}
        onSubmit={(name) => {
          saveReviewer(name);
          setReviewer(name);
        }}
      />
    );
  }

  const key = `${reviewer}:${routeKey(route)}`;
  return (
    <Screen resetKey={key}>
      <Content key={key} reviewer={reviewer} route={route} />
    </Screen>
  );
}

function Content({ reviewer, route }: { reviewer: string; route: Route }) {
  switch (route.name) {
    case "screening":
      return <Validator reviewer={reviewer} />;
    case "papers":
      return <PaperPicker reviewer={reviewer} />;
    case "tour":
      return <TourScreen reviewer={reviewer} />;
    case "classification":
      return (
        <ClassificationReview
          reviewer={reviewer}
          quickRef={route.quickRef}
          mode={route.mode}
          source={airtableSource({
            quickRef: route.quickRef,
            reviewer,
            mode: route.mode,
          })}
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
    <ErrorBoundary FallbackComponent={ErrorScreen} resetKeys={[resetKey]}>
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
