import "@mantine/core/styles.css";
import { createTheme, MantineProvider } from "@mantine/core";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "@/components/App";

const theme = createTheme({});

const root = document.getElementById("root");
if (root === null) {
  throw new Error("Root element not found");
}

createRoot(root).render(
  <StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="auto">
      <App />
    </MantineProvider>
  </StrictMode>,
);
