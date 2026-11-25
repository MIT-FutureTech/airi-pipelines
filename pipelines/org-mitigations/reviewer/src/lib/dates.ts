import type { DatePrecision } from "@/lib/types";

const FORMATS: Record<DatePrecision, Intl.DateTimeFormatOptions> = {
  day: { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" },
  month: { month: "short", year: "numeric", timeZone: "UTC" },
  year: { year: "numeric", timeZone: "UTC" },
};

export function formatDate(
  date: string | null,
  precision: DatePrecision | null,
): string {
  if (date === null || precision === null) {
    return "Undated";
  }
  return new Date(date).toLocaleDateString("en-GB", FORMATS[precision]);
}
