import type { Decision } from "@api/_shared";
import { type CSSVariablesResolver, createTheme } from "@mantine/core";

export const theme = createTheme({
  colors: {
    neutral: [
      "#f1f4fe",
      "#e4e6ed",
      "#c8cad3",
      "#a9adb9", // deselected text
      "#9094a3",
      "#7f8496",
      "#777c91", // deselected background
      "#63687c",
      "#cccccc", // selected background
      "#ffffff",
    ],
  },
});

export const cssVariablesResolver: CSSVariablesResolver = (mantineTheme) => ({
  variables: {},
  light: { "--mantine-color-dimmed": mantineTheme.colors.gray[7] },
  dark: { "--mantine-color-dimmed": mantineTheme.colors.dark[1] },
});

export const DECISION_COLORS: Record<Decision, string> = {
  include: "green",
  exclude: "neutral",
  uncertain: "yellow",
};
