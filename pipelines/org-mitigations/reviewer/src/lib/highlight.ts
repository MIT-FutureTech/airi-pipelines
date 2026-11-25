import type { Span } from "@/lib/types";

export interface HighlightWindow {
  before: string;
  highlight: string;
  after: string;
}

export function highlightWindow(
  text: string,
  span: Span,
  context: number,
): HighlightWindow {
  const start = startOfWord(
    text,
    Math.max(0, span.start - context),
    span.start,
  );
  const end = endOfWord(
    text,
    Math.min(text.length, span.end + context),
    span.end,
  );
  return {
    before: `${start > 0 ? "…" : ""}${text.slice(start, span.start)}`,
    highlight: text.slice(span.start, span.end),
    after: `${text.slice(span.end, end)}${end < text.length ? "…" : ""}`,
  };
}

function startOfWord(text: string, at: number, limit: number): number {
  if (at === 0 || /\s/.test(text.charAt(at - 1))) {
    return at;
  }
  const offset = text.slice(at, limit).search(/\s/);
  return offset === -1 ? at : at + offset + 1;
}

function endOfWord(text: string, at: number, limit: number): number {
  if (at === text.length || /\s/.test(text.charAt(at))) {
    return at;
  }
  const offset = text.slice(limit, at).search(/\s\S*$/);
  return offset === -1 ? at : limit + offset;
}
