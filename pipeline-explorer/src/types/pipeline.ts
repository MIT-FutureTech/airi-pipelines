export type NodeType =
  | "processor"
  | "datastore"
  | "external-service"
  | "manual-step"
  | "proposed";

export type DetailStatus = "verified" | "unverified" | "no-details";

export const detailStatusConfig: Record<
  DetailStatus,
  { icon: string; label: string; tooltip: string }
> = {
  verified: {
    icon: "\u2713",
    label: "\u2713 Verified",
    tooltip: "The details for this node have been verified to be accurate.",
  },
  unverified: {
    icon: "?",
    label: "? Unverified",
    tooltip:
      "The details for this node have not yet been verified and may not be entirely accurate.",
  },
  "no-details": {
    icon: "",
    label: "No details",
    tooltip: "No details have been documented for this node yet.",
  },
};

export interface PipelineNode {
  id: string;
  label: string;
  type: NodeType;
  verified: boolean;
  link?: { url: string; label: string };
}

export interface PipelineEdge {
  source: string;
  target: string;
  label?: string;
}

export interface PipelineDefinition {
  id: string;
  name: string;
  description: string;
  /** Nodes owned by this pipeline: displayed inside its group box */
  nodes: PipelineNode[];
  /** Shared nodes this pipeline connects to */
  shared: PipelineNode[];
  /** Edges involving this pipeline's own and shared nodes */
  edges: PipelineEdge[];
}
