// biome-ignore-all lint/style/useNamingConvention: keys mirror Python values
import type { OutcomeClass } from "@/lib/types";

export const OUTCOME_ORDER: OutcomeClass[] = [
  "false_negative",
  "false_positive",
  "true_positive",
  "true_negative",
  "unlabeled",
];

export const OUTCOME_LABELS: Record<OutcomeClass, string> = {
  false_negative: "FN",
  false_positive: "FP",
  true_positive: "TP",
  true_negative: "TN",
  unlabeled: "?",
};

export const OUTCOME_COLORS: Record<OutcomeClass, string> = {
  false_negative: "red",
  false_positive: "orange",
  true_positive: "green",
  true_negative: "teal",
  unlabeled: "gray",
};

export function countOutcomes(
  outcomes: Iterable<OutcomeClass>,
): Record<OutcomeClass, number> {
  const counts: Record<OutcomeClass, number> = {
    false_negative: 0,
    false_positive: 0,
    true_positive: 0,
    true_negative: 0,
    unlabeled: 0,
  };
  for (const outcome of outcomes) {
    counts[outcome] += 1;
  }
  return counts;
}
