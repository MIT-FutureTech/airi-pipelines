import type { Bundle } from "@/lib/types";

const BUNDLE_PATH = "/data/bundle.json";

async function fetchBundle(): Promise<Bundle> {
  const response = await fetch(BUNDLE_PATH);
  if (!response.ok) {
    throw new Error(`Failed to load ${BUNDLE_PATH}: HTTP ${response.status}`);
  }
  return (await response.json()) as Bundle;
}

let bundle: Promise<Bundle> | undefined;

export function getBundle(): Promise<Bundle> {
  bundle ??= fetchBundle();
  return bundle;
}
