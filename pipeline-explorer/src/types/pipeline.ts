export type NodeType =
  | "repo"
  | "datastore"
  | "external-service"
  | "manual-step"
  | "proposed";

export interface PipelineNode {
  id: string;
  label: string;
  type: NodeType;
  position: { x: number; y: number };
  url?: string;
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
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}
