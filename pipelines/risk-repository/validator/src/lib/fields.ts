// Runtime field lists for the browser. The frontend imports only TYPES from
// api/_classification (erased at build time). Importing its runtime values would
// make the browser fetch /api/*.ts, which `vercel dev` routes to the serverless
// functions runtime, returning 404 and breaking the page.
import type { ReviewField, RiskOrigin } from "@api/_classification";

export const REVIEW_FIELDS: readonly ReviewField[] = [
  "validity",
  "entity",
  "intent",
  "timing",
  "subdomain",
];

export const AXIS_FIELDS: readonly ReviewField[] = [
  "entity",
  "intent",
  "timing",
  "subdomain",
];

export const REJECTED_ORIGIN: RiskOrigin = "model-added, human-rejected";

export const NOT_A_RISK = "not-a-risk";
