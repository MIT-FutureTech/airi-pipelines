import { useState } from "react";
import type { HighlightGroup } from "@/lib/highlight";
import {
  type HighlightScope,
  loadHighlightGroups,
  saveHighlightGroups,
} from "@/lib/storage";

export interface HighlightState {
  groups: HighlightGroup[];
  setGroups: (groups: HighlightGroup[]) => void;
  drawerOpen: boolean;
  toggleDrawer: () => void;
  closeDrawer: () => void;
}

export function useHighlightGroups(scope: HighlightScope): HighlightState {
  const [groups, storeGroups] = useState<HighlightGroup[]>(() =>
    loadHighlightGroups(scope),
  );
  const [drawerOpen, setDrawerOpen] = useState(false);

  return {
    groups,
    setGroups: (next) => {
      storeGroups(next);
      saveHighlightGroups(scope, next);
    },
    drawerOpen,
    toggleDrawer: () => {
      setDrawerOpen((open) => !open);
    },
    closeDrawer: () => {
      setDrawerOpen(false);
    },
  };
}
