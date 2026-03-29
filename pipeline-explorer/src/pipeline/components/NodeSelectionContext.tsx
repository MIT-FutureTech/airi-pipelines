"use client";

import { createContext, useContext } from "react";

const NodeSelectionContext = createContext<(nodeId: string) => void>(() => {});

export const NodeSelectionProvider = NodeSelectionContext.Provider;

export function useSelectNode() {
  return useContext(NodeSelectionContext);
}
