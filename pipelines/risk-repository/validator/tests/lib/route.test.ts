import { describe, expect, it } from "vitest";
import { formatRoute, parseRoute, type Route, routeKey } from "@/lib/route";

const ORIGIN = "https://validator.test";

function parse(path: string): Route {
  return parseRoute(new URL(path, ORIGIN).href);
}

const ROUTES: Route[] = [
  { name: "tasks" },
  { name: "screening" },
  { name: "papers" },
  { name: "tour" },
  { name: "classification", quickRef: "Lee2025", mode: "blind" },
  { name: "classification", quickRef: "Lee2025", mode: "anchored" },
];

describe("parseRoute", () => {
  it("reads the top-level screens", () => {
    expect(parse("/")).toEqual({ name: "tasks" });
    expect(parse("/screening")).toEqual({ name: "screening" });
    expect(parse("/papers")).toEqual({ name: "papers" });
    expect(parse("/tour")).toEqual({ name: "tour" });
  });

  it("falls back to tasks for a path it does not know", () => {
    expect(parse("/nowhere")).toEqual({ name: "tasks" });
  });

  it("ignores a trailing slash", () => {
    expect(parse("/papers/")).toEqual({ name: "papers" });
    expect(parse("/screening/")).toEqual({ name: "screening" });
  });

  it("reads a paper together with its mode", () => {
    expect(parse("/papers/Lee2025?mode=blind")).toEqual({
      name: "classification",
      quickRef: "Lee2025",
      mode: "blind",
    });
    expect(parse("/papers/Lee2025?mode=anchored")).toEqual({
      name: "classification",
      quickRef: "Lee2025",
      mode: "anchored",
    });
  });

  it("decodes a quick ref that needed escaping", () => {
    const route = parse("/papers/Lee%202025?mode=blind");
    expect(route).toMatchObject({ quickRef: "Lee 2025" });
  });

  it("refuses a paper with no mode", () => {
    expect(() => parse("/papers/Lee2025")).toThrow("Invalid mode");
  });

  it("refuses a mode it does not recognise", () => {
    expect(() => parse("/papers/Lee2025?mode=sighted")).toThrow("Invalid mode");
  });
});

describe("formatRoute", () => {
  it("writes the top-level screens", () => {
    expect(formatRoute({ name: "tasks" })).toBe("/");
    expect(formatRoute({ name: "screening" })).toBe("/screening");
    expect(formatRoute({ name: "papers" })).toBe("/papers");
    expect(formatRoute({ name: "tour" })).toBe("/tour");
  });

  it("writes a paper together with its mode", () => {
    expect(
      formatRoute({
        name: "classification",
        quickRef: "Lee2025",
        mode: "blind",
      }),
    ).toBe("/papers/Lee2025?mode=blind");
  });

  it("escapes a quick ref that needs it", () => {
    expect(
      formatRoute({
        name: "classification",
        quickRef: "Lee 2025",
        mode: "blind",
      }),
    ).toBe("/papers/Lee%202025?mode=blind");
  });
});

describe("formatRoute and parseRoute together", () => {
  it("round-trips every kind of route", () => {
    for (const route of ROUTES) {
      expect(parse(formatRoute(route))).toEqual(route);
    }
  });

  it("round-trips a quick ref that needs escaping", () => {
    const route: Route = {
      name: "classification",
      quickRef: "Lee 2025/a",
      mode: "anchored",
    };
    expect(parse(formatRoute(route))).toEqual(route);
  });
});

describe("routeKey", () => {
  it("names the top-level screens after themselves", () => {
    expect(routeKey({ name: "tasks" })).toBe("tasks");
    expect(routeKey({ name: "papers" })).toBe("papers");
  });

  it("separates one paper and mode from another", () => {
    const keys = new Set(ROUTES.map(routeKey));
    expect(keys.size).toBe(ROUTES.length);
  });
});
