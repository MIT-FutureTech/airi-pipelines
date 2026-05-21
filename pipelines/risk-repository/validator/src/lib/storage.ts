const REVIEWER_KEY = "validator.reviewer";

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
