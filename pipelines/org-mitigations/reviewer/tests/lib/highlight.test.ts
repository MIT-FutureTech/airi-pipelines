import { describe, expect, it } from "vitest";
import { highlightWindow } from "@/lib/highlight";

const TEXT = "one two three four five SIX six seven eight nine ten";

function spanOf(quote: string) {
  const start = TEXT.indexOf(quote);
  return { start, end: start + quote.length };
}

describe("highlightWindow", () => {
  it("cuts the context at whole words and marks the cuts", () => {
    expect(highlightWindow(TEXT, spanOf("SIX"), 7)).toEqual({
      before: "…five ",
      highlight: "SIX",
      after: " six…",
    });
  });

  it("leaves no mark at the start of the text", () => {
    expect(highlightWindow(TEXT, spanOf("one"), 5)).toEqual({
      before: "",
      highlight: "one",
      after: " two…",
    });
  });

  it("shows the whole text when the context covers it", () => {
    expect(highlightWindow(TEXT, spanOf("SIX"), 100)).toEqual({
      before: "one two three four five ",
      highlight: "SIX",
      after: " six seven eight nine ten",
    });
  });
});
