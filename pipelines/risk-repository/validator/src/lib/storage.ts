import type { HighlightGroup } from "./highlight";

const REVIEWER_KEY = "validator.reviewer";
const HIGHLIGHT_GROUPS_KEY = "validator.highlightGroups";

export function loadReviewer(): string | null {
  const value = window.localStorage.getItem(REVIEWER_KEY);
  if (value === null || value.trim() === "") {
    return null;
  }
  return value;
}

export function saveReviewer(name: string): void {
  window.localStorage.setItem(REVIEWER_KEY, name);
}

export function clearReviewer(): void {
  window.localStorage.removeItem(REVIEWER_KEY);
}

export function loadHighlightGroups(): HighlightGroup[] {
  const value = window.localStorage.getItem(HIGHLIGHT_GROUPS_KEY);
  if (value === null) {
    return [];
  }
  return JSON.parse(value) as HighlightGroup[];
}

export function saveHighlightGroups(groups: HighlightGroup[]): void {
  window.localStorage.setItem(HIGHLIGHT_GROUPS_KEY, JSON.stringify(groups));
}
