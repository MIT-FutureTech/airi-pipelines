import type { Decision } from "@api/_shared";

export const DECISION_COLORS: Record<Decision, string> = {
  include: "green",
  exclude: "gray",
  uncertain: "yellow",
};
