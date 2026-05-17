import type { AuditBundle, Manifest } from "@/lib/types";

const BUNDLES_BASE = "/bundles";

async function fetchJson<T>(path: string, label: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${label}: HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

const cache = new Map<string, Promise<unknown>>();

function memoized<T>(key: string, factory: () => Promise<T>): Promise<T> {
  let promise = cache.get(key);
  if (promise === undefined) {
    promise = factory();
    cache.set(key, promise);
  }
  return promise as Promise<T>;
}

export function getManifest(): Promise<Manifest> {
  return memoized("manifest", () =>
    fetchJson<Manifest>(`${BUNDLES_BASE}/manifest.json`, "manifest"),
  );
}

export function getBundle(filename: string): Promise<AuditBundle> {
  return memoized(`bundle:${filename}`, () =>
    fetchJson<AuditBundle>(`${BUNDLES_BASE}/${filename}`, `bundle ${filename}`),
  );
}
