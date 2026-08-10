import type { ReviewField } from "@shared/classification";
import { SUBDOMAIN_LABELS } from "@/lib/subdomains";

export interface AxisOption {
  value: string;
  label: string;
}

export interface CausalAxis {
  field: ReviewField;
  label: string;
  options: AxisOption[];
}

export const CAUSAL_AXES: CausalAxis[] = [
  {
    field: "entity",
    label: "Entity",
    options: [
      { value: "human", label: "Human" },
      { value: "ai", label: "AI" },
      { value: "other", label: "Other" },
    ],
  },
  {
    field: "intent",
    label: "Intent",
    options: [
      { value: "intentional", label: "Intentional" },
      { value: "unintentional", label: "Unintentional" },
      { value: "other", label: "Other" },
    ],
  },
  {
    field: "timing",
    label: "Timing",
    options: [
      { value: "pre-deployment", label: "Pre-deployment" },
      { value: "post-deployment", label: "Post-deployment" },
      { value: "other", label: "Other" },
    ],
  },
];

export const FIELD_LABELS: Record<ReviewField, string> = {
  validity: "Validity",
  entity: "Entity",
  intent: "Intent",
  timing: "Timing",
  subdomain: "Subdomain",
};

export function valueLabel(field: ReviewField, value: string): string {
  if (field === "subdomain") {
    return SUBDOMAIN_LABELS[value] ?? value;
  }
  const axis = CAUSAL_AXES.find((axis) => axis.field === field);
  const option = axis?.options.find((option) => option.value === value);
  return option?.label ?? value;
}
