import { REVIEW_MODES, type ReviewMode } from "@shared/classification";
import { useSyncExternalStore } from "react";

export type Route =
  | { name: "tasks" }
  | { name: "screening" }
  | { name: "papers" }
  | { name: "classification"; quickRef: string; mode: ReviewMode };

export function routeKey(route: Route): string {
  return route.name === "classification"
    ? `classification:${route.quickRef}:${route.mode}`
    : route.name;
}

export function useRoute(): Route {
  return parseRoute(useSyncExternalStore(subscribe, getSnapshot));
}

export function navigate(route: Route): void {
  window.history.pushState(null, "", formatRoute(route));
  for (const listener of listeners) {
    listener();
  }
}

const listeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  window.addEventListener("popstate", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("popstate", listener);
  };
}

function getSnapshot(): string {
  return window.location.href;
}

function parseRoute(href: string): Route {
  const url = new URL(href);
  const segments = url.pathname.split("/").filter((segment) => segment !== "");
  if (segments[0] === "screening") {
    return { name: "screening" };
  }
  if (segments[0] === "papers") {
    if (segments.length === 1) {
      return { name: "papers" };
    }
    return {
      name: "classification",
      quickRef: decodeURIComponent(segments[1]),
      mode: parseMode(url.searchParams.get("mode")),
    };
  }
  return { name: "tasks" };
}

function formatRoute(route: Route): string {
  switch (route.name) {
    case "tasks":
      return "/";
    case "screening":
      return "/screening";
    case "papers":
      return "/papers";
    case "classification":
      return `/papers/${encodeURIComponent(route.quickRef)}?mode=${route.mode}`;
  }
}

function parseMode(value: string | null): ReviewMode {
  const mode = REVIEW_MODES.find((mode) => mode === value);
  if (mode === undefined) {
    throw new Error(`Invalid mode: ${value}`);
  }
  return mode;
}
