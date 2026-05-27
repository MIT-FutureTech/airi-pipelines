export interface HighlightGroup {
  id: string;
  color: string;
  keywords: string;
  caseSensitive: boolean;
  wholeWord: boolean;
}

export interface HighlightChunk {
  text: string;
  color: string | null;
}

export const HIGHLIGHT_PALETTE: string[] = [
  "red",
  "orange",
  "yellow",
  "lime",
  "green",
  "teal",
  "cyan",
  "blue",
  "violet",
  "pink",
];

export const MAX_HIGHLIGHT_GROUPS = 10;

const REGEX_SPECIAL_CHARS = /[.*+?^${}()|[\]\\]/g;

function escapeRegex(value: string): string {
  return value.replace(REGEX_SPECIAL_CHARS, "\\$&");
}

function parseKeywords(raw: string): string[] {
  return raw
    .split(/\r?\n/)
    .map((k) => k.trim())
    .filter((k) => k !== "");
}

function buildGroupRegex(group: HighlightGroup): RegExp | null {
  const keywords = parseKeywords(group.keywords);
  if (keywords.length === 0) {
    return null;
  }
  const alternation = keywords.map(escapeRegex).join("|");
  const pattern = group.wholeWord
    ? `\\b(?:${alternation})\\b`
    : `(?:${alternation})`;
  const flags = group.caseSensitive ? "g" : "gi";
  return new RegExp(pattern, flags);
}

interface Match {
  start: number;
  end: number;
  color: string;
}

export function highlightText(
  text: string,
  groups: HighlightGroup[],
): HighlightChunk[] {
  if (text === "") {
    return [];
  }
  const matches: Match[] = [];
  for (const group of groups) {
    const regex = buildGroupRegex(group);
    if (regex === null) {
      continue;
    }
    for (const m of text.matchAll(regex)) {
      if (m.index === undefined) {
        continue;
      }
      matches.push({
        start: m.index,
        end: m.index + m[0].length,
        color: group.color,
      });
    }
  }
  if (matches.length === 0) {
    return [{ text, color: null }];
  }
  matches.sort(
    (a, b) => a.start - b.start || b.end - b.start - (a.end - a.start),
  );
  const filtered: Match[] = [];
  let lastEnd = 0;
  for (const m of matches) {
    if (m.start < lastEnd) {
      continue;
    }
    filtered.push(m);
    lastEnd = m.end;
  }
  const chunks: HighlightChunk[] = [];
  let cursor = 0;
  for (const m of filtered) {
    if (m.start > cursor) {
      chunks.push({ text: text.slice(cursor, m.start), color: null });
    }
    chunks.push({ text: text.slice(m.start, m.end), color: m.color });
    cursor = m.end;
  }
  if (cursor < text.length) {
    chunks.push({ text: text.slice(cursor), color: null });
  }
  return chunks;
}
