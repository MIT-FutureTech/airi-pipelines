import "@mantine/core/styles.css";
import { MantineProvider } from "@mantine/core";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";
import { App } from "@/components/App";
import { ErrorScreen } from "@/components/ErrorScreen";
import { cssVariablesResolver, theme } from "@/lib/theme";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("Root element not found");
}

createRoot(root).render(
  <StrictMode>
    <MantineProvider
      theme={theme}
      cssVariablesResolver={cssVariablesResolver}
      defaultColorScheme="auto"
    >
      <ErrorBoundary FallbackComponent={ErrorScreen}>
        <App />
      </ErrorBoundary>
    </MantineProvider>
  </StrictMode>,
);
