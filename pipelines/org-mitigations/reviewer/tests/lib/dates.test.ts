import { describe, expect, it } from "vitest";
import { formatDate } from "@/lib/dates";

describe("formatDate", () => {
  it("shows the day, month and year for day precision", () => {
    expect(formatDate("2026-02-24", "day")).toBe("24 Feb 2026");
  });

  it("shows the month and year for month precision", () => {
    expect(formatDate("2025-03-01", "month")).toBe("Mar 2025");
  });

  it("shows only the year for year precision", () => {
    expect(formatDate("2025-06-30", "year")).toBe("2025");
  });

  it("marks a document with no date as undated", () => {
    expect(formatDate(null, null)).toBe("Undated");
  });
});
