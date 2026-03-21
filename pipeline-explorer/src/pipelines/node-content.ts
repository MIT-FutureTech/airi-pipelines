import type { ComponentType } from "react";

// Registry mapping node IDs to their MDX content components.
// When adding a new MDX file, import it here and add it to the map.

import Scraper from "./example-pipeline/scraper.mdx";
import Classifier from "./example-pipeline/classifier.mdx";

const nodeContent: Record<string, ComponentType> = {
  scraper: Scraper,
  classifier: Classifier,
};

export function getNodeContent(nodeId: string): ComponentType | null {
  return nodeContent[nodeId] ?? null;
}
