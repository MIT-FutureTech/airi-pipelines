import { queryParam } from "@api/_http";
import { describe, expect, it } from "vitest";

describe("queryParam", () => {
  it("returns a trimmed parameter", () => {
    expect(queryParam(new URLSearchParams("reviewer=alice"), "reviewer")).toBe(
      "alice",
    );
    expect(
      queryParam(new URLSearchParams("reviewer=%20alice%20"), "reviewer"),
    ).toBe("alice");
  });

  it("treats a missing parameter as absent", () => {
    expect(queryParam(new URLSearchParams(""), "reviewer")).toBeNull();
  });

  it("treats a blank parameter as absent", () => {
    expect(queryParam(new URLSearchParams("reviewer="), "reviewer")).toBeNull();
    expect(
      queryParam(new URLSearchParams("reviewer=%20%20"), "reviewer"),
    ).toBeNull();
  });

  it("refuses a parameter that was given more than once", () => {
    expect(
      queryParam(
        new URLSearchParams("reviewer=alice&reviewer=bob"),
        "reviewer",
      ),
    ).toBeNull();
  });
});
