import type { CSSProperties } from "react";
import type { Quote, Strength } from "@/lib/types";

export const STRENGTHS: Strength[] = ["described", "stated", "reference"];

export const STRENGTH_LABELS: Record<Strength, string> = {
  described: "Described",
  stated: "Stated",
  reference: "Reference",
};

// Stronger is darker in light mode and lighter in dark mode
export const STRENGTH_COLORS: Record<Strength, CSSProperties> = {
  described: {
    backgroundColor: "light-dark(#1c5cab, #86b6ef)",
    color: "light-dark(#ffffff, #000000)",
  },
  stated: {
    backgroundColor: "#3987e5",
    color: "#ffffff",
  },
  reference: {
    backgroundColor: "light-dark(#86b6ef, #1c5cab)",
    color: "light-dark(#000000, #ffffff)",
  },
};

export function sortByStrength(evidence: Quote[]): Quote[] {
  return evidence.toSorted(
    (a, b) => STRENGTHS.indexOf(a.strength) - STRENGTHS.indexOf(b.strength),
  );
}

export function strongest(evidence: Quote[]): Strength {
  const strength = STRENGTHS.find((candidate) =>
    evidence.some((item) => item.strength === candidate),
  );
  if (strength === undefined) {
    throw new Error("No evidence to rate");
  }
  return strength;
}
