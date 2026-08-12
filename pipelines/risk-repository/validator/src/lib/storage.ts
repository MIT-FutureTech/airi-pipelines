import type { ReviewMode } from "@shared/classification";
import type { HighlightGroup } from "./highlight";

const REVIEWER_KEY = "validator.reviewer";
const HIGHLIGHT_GROUPS_KEY = "validator.highlightGroups";
const PAPER_PICKER_KEY = "validator.paperPicker";

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

export interface PaperPickerPrefs {
  mode: ReviewMode;
  assignee: string | null;
  status: string | null;
}

export function loadPaperPickerPrefs(): PaperPickerPrefs {
  const value = window.localStorage.getItem(PAPER_PICKER_KEY);
  if (value === null) {
    return { mode: "anchored", assignee: null, status: null };
  }
  return JSON.parse(value) as PaperPickerPrefs;
}

export function savePaperPickerPrefs(prefs: PaperPickerPrefs): void {
  window.localStorage.setItem(PAPER_PICKER_KEY, JSON.stringify(prefs));
}
