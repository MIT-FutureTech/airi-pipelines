import { describe, expect, it } from "vitest";
import { type HighlightGroup, highlightText } from "@/lib/highlight";

function group(
  keywords: string,
  color: string,
  options: { caseSensitive?: boolean; wholeWord?: boolean } = {},
): HighlightGroup {
  return {
    id: `group-${color}`,
    color,
    keywords,
    caseSensitive: options.caseSensitive ?? false,
    wholeWord: options.wholeWord ?? false,
  };
}

describe("highlightText with nothing to highlight", () => {
  it("returns nothing for empty text", () => {
    expect(highlightText("", [group("cat", "red")])).toEqual([]);
  });

  it("returns the text whole when no group is given", () => {
    expect(highlightText("a sentence", [])).toEqual([
      { text: "a sentence", color: null },
    ]);
  });

  it("ignores a group with no keywords", () => {
    expect(highlightText("a sentence", [group("  \n  ", "red")])).toEqual([
      { text: "a sentence", color: null },
    ]);
  });

  it("returns the text whole when nothing matches", () => {
    expect(highlightText("a sentence", [group("dog", "red")])).toEqual([
      { text: "a sentence", color: null },
    ]);
  });
});

describe("highlightText splitting", () => {
  it("splits the text around a match", () => {
    expect(highlightText("the cat sat", [group("cat", "red")])).toEqual([
      { text: "the ", color: null },
      { text: "cat", color: "red" },
      { text: " sat", color: null },
    ]);
  });

  it("keeps a match at the very start or end", () => {
    expect(highlightText("cat", [group("cat", "red")])).toEqual([
      { text: "cat", color: "red" },
    ]);
  });

  it("marks every occurrence", () => {
    expect(highlightText("cat and cat", [group("cat", "red")])).toEqual([
      { text: "cat", color: "red" },
      { text: " and ", color: null },
      { text: "cat", color: "red" },
    ]);
  });

  it("reads one keyword per line", () => {
    expect(highlightText("cat dog", [group("cat\ndog", "red")])).toEqual([
      { text: "cat", color: "red" },
      { text: " ", color: null },
      { text: "dog", color: "red" },
    ]);
  });

  it("colours each group separately", () => {
    const groups = [group("cat", "red"), group("dog", "blue")];
    expect(highlightText("cat dog", groups)).toEqual([
      { text: "cat", color: "red" },
      { text: " ", color: null },
      { text: "dog", color: "blue" },
    ]);
  });
});

describe("highlightText matching rules", () => {
  it("ignores case by default", () => {
    expect(highlightText("CAT", [group("cat", "red")])).toEqual([
      { text: "CAT", color: "red" },
    ]);
  });

  it("respects case when asked to", () => {
    const groups = [group("cat", "red", { caseSensitive: true })];
    expect(highlightText("CAT", groups)).toEqual([
      { text: "CAT", color: null },
    ]);
  });

  it("matches inside a longer word by default", () => {
    expect(highlightText("category", [group("cat", "red")])).toEqual([
      { text: "cat", color: "red" },
      { text: "egory", color: null },
    ]);
  });

  it("stops at word boundaries when asked to", () => {
    const groups = [group("cat", "red", { wholeWord: true })];
    expect(highlightText("category", groups)).toEqual([
      { text: "category", color: null },
    ]);
    expect(highlightText("a cat.", groups)).toEqual([
      { text: "a ", color: null },
      { text: "cat", color: "red" },
      { text: ".", color: null },
    ]);
  });

  it("treats keywords as literal text, not as patterns", () => {
    expect(highlightText("axb", [group("a.b", "red")])).toEqual([
      { text: "axb", color: null },
    ]);
    expect(highlightText("a.b", [group("a.b", "red")])).toEqual([
      { text: "a.b", color: "red" },
    ]);
  });
});

describe("highlightText overlap resolution", () => {
  it("prefers the longer of two matches starting together", () => {
    const groups = [group("ab", "blue"), group("abc", "red")];
    expect(highlightText("abcd", groups)).toEqual([
      { text: "abc", color: "red" },
      { text: "d", color: null },
    ]);
  });

  it("drops a match that starts inside an earlier one", () => {
    const groups = [group("abc", "red"), group("cde", "blue")];
    expect(highlightText("abcde", groups)).toEqual([
      { text: "abc", color: "red" },
      { text: "de", color: null },
    ]);
  });

  it("keeps a match that starts exactly where the previous one ended", () => {
    const groups = [group("ab", "red"), group("cd", "blue")];
    expect(highlightText("abcd", groups)).toEqual([
      { text: "ab", color: "red" },
      { text: "cd", color: "blue" },
    ]);
  });
});
