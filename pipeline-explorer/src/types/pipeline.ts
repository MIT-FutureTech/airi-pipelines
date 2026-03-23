export type NodeType =
  | "processor"
  | "datastore"
  | "external-service"
  | "manual-step"
  | "proposed";

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
