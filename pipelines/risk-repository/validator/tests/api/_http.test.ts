import { queryString } from "@api/_http";
import { describe, expect, it } from "vitest";

describe("queryString", () => {
  it("returns a trimmed parameter", () => {
    expect(queryString("alice")).toBe("alice");
    expect(queryString("  alice  ")).toBe("alice");
  });

  it("treats a missing parameter as absent", () => {
    expect(queryString(undefined)).toBeNull();
  });

  it("treats a blank parameter as absent", () => {
    expect(queryString("")).toBeNull();
    expect(queryString("   ")).toBeNull();
  });

  it("refuses a parameter that was given more than once", () => {
    expect(queryString(["alice", "bob"])).toBeNull();
    expect(queryString(["alice"])).toBeNull();
  });
});
