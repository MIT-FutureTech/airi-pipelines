import type { LocatedEvidence, Strength } from "@/lib/types";

export const STRENGTHS: Strength[] = ["described", "stated", "reference"];

export function strongest(evidence: LocatedEvidence[]): Strength {
  const strength = STRENGTHS.find((candidate) =>
    evidence.some((item) => item.strength === candidate),
  );
  if (strength === undefined) {
    throw new Error("No evidence to rate");
  }
  return strength;
}
