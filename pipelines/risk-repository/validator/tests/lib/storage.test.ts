import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { HighlightGroup } from "@/lib/highlight";
import {
  clearReviewer,
  hasSeenTour,
  loadHighlightGroups,
  loadPaperPickerPrefs,
  loadReviewer,
  markTourSeen,
  saveHighlightGroups,
  savePaperPickerPrefs,
  saveReviewer,
} from "@/lib/storage";

let store: Map<string, string>;

beforeEach(() => {
  store = new Map();
  vi.stubGlobal("window", {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    },
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const GROUP: HighlightGroup = {
  id: "g1",
  color: "red",
  keywords: "cat",
  caseSensitive: false,
  wholeWord: true,
};

describe("the reviewer's name", () => {
  it("is absent before anyone signs in", () => {
    expect(loadReviewer()).toBeNull();
  });

  it("comes back after being saved", () => {
    saveReviewer("alice");
    expect(loadReviewer()).toBe("alice");
  });

  it("is absent again once cleared", () => {
    saveReviewer("alice");
    clearReviewer();
    expect(loadReviewer()).toBeNull();
  });

  it("treats a blank stored name as absent", () => {
    saveReviewer("   ");
    expect(loadReviewer()).toBeNull();
  });

  it("returns a stored name exactly as it was saved", () => {
    saveReviewer("  alice  ");
    expect(loadReviewer()).toBe("  alice  ");
  });
});

describe("the tour", () => {
  it("has not been seen to begin with", () => {
    expect(hasSeenTour()).toBe(false);
  });

  it("stays seen once marked", () => {
    markTourSeen();
    expect(hasSeenTour()).toBe(true);
  });
});

describe("highlight groups", () => {
  it("start out empty", () => {
    expect(loadHighlightGroups("screening")).toEqual([]);
    expect(loadHighlightGroups("classification")).toEqual([]);
  });

  it("come back as they were saved", () => {
    saveHighlightGroups("screening", [GROUP]);
    expect(loadHighlightGroups("screening")).toEqual([GROUP]);
  });

  it("are kept apart between screening and classification", () => {
    saveHighlightGroups("screening", [GROUP]);
    expect(loadHighlightGroups("classification")).toEqual([]);

    const other = { ...GROUP, id: "g2", keywords: "dog" };
    saveHighlightGroups("classification", [other]);
    expect(loadHighlightGroups("screening")).toEqual([GROUP]);
    expect(loadHighlightGroups("classification")).toEqual([other]);
  });

  it("fail loudly rather than silently resetting when the store is corrupt", () => {
    store.set("validator.highlightGroups", "{not json");
    expect(() => loadHighlightGroups("screening")).toThrow();
  });
});

describe("paper picker preferences", () => {
  it("start on anchored mode with no filters", () => {
    expect(loadPaperPickerPrefs()).toEqual({
      mode: "anchored",
      assignee: null,
      status: null,
    });
  });

  it("come back as they were saved", () => {
    const prefs = {
      mode: "blind" as const,
      assignee: "alice",
      status: "In Progress",
    };
    savePaperPickerPrefs(prefs);
    expect(loadPaperPickerPrefs()).toEqual(prefs);
  });

  it("fail loudly rather than silently resetting when the store is corrupt", () => {
    store.set("validator.paperPicker", "{not json");
    expect(() => loadPaperPickerPrefs()).toThrow();
  });
});

describe("the stored keys", () => {
  it("are namespaced to the app", () => {
    saveReviewer("alice");
    markTourSeen();
    saveHighlightGroups("screening", [GROUP]);
    saveHighlightGroups("classification", [GROUP]);
    savePaperPickerPrefs({ mode: "blind", assignee: null, status: null });
    for (const key of store.keys()) {
      expect(key.startsWith("validator.")).toBe(true);
    }
  });
});
