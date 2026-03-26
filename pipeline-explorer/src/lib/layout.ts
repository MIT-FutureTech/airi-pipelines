import dagre from "@dagrejs/dagre";
import type { Edge, Node } from "@xyflow/react";
import { hasNodeContent } from "@/pipelines/node-content";
import type {
  DetailStatus,
  PipelineDefinition,
  PipelineNode,
} from "@/types/pipeline";

function getPosition(
  map: Map<string, { x: number; y: number }>,
  id: string,
): { x: number; y: number } {
  const pos = map.get(id);
  if (pos === undefined) {
    throw new Error(`Missing position for node "${id}"`);
  }
  return pos;
}

/** Estimated node dimensions for dagre layout */
const NODE_WIDTH = 220;
const NODE_HEIGHT = 60;
/** Padding inside the group box around the outermost nodes */
const GROUP_PADDING = 30;
/** Space reserved at top of group for the label */
const GROUP_LABEL_HEIGHT = 36;

/**
 * Build the full React Flow graph from all pipelines + shared nodes.
 *
 * 1. Feed every node and edge into a single dagre layout
 * 2. Compute group boxes from each pipeline's owned-node positions
 * 3. Convert owned nodes to relative positions inside their group
 * 4. Shared nodes stay at absolute positions (no group parent)
 */
export function buildNodesAndEdges(
  pipelines: PipelineDefinition[],
  sharedNodes: PipelineNode[],
) {
  const absPositions = runDagreLayout(pipelines, sharedNodes);

  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];

  for (const pipeline of pipelines) {
    const { groupNode, childNodes } = buildPipelineGroup(
      pipeline,
      absPositions,
    );
    allNodes.push(groupNode, ...childNodes);
  }

  for (const node of sharedNodes) {
    allNodes.push(toFlowNode(node, getPosition(absPositions, node.id)));
  }

  const seenEdges = new Set<string>();
  for (const pipeline of pipelines) {
    for (const edge of pipeline.edges) {
      const edgeKey = `${edge.source}-${edge.target}`;
      if (seenEdges.has(edgeKey)) {
        continue;
      }
      seenEdges.add(edgeKey);
      allEdges.push({
        id: edgeKey,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: false,
        style: { stroke: "#9ca3af" },
        labelStyle: { fontSize: 11, fill: "#9ca3af" },
      });
    }
  }

  return { allNodes, allEdges };
}

export function findNode(
  nodeId: string,
  pipelines: PipelineDefinition[],
  sharedNodes: PipelineNode[],
): PipelineNode | null {
  for (const node of sharedNodes) {
    if (node.id === nodeId) {
      return node;
    }
  }
  for (const p of pipelines) {
    const node = p.nodes.find((n) => n.id === nodeId);
    if (node) {
      return node;
    }
  }
  return null;
}

function resolveDetailStatus(node: PipelineNode): DetailStatus {
  if (!hasNodeContent(node.id)) {
    return "no-details";
  }
  return node.verified ? "verified" : "unverified";
}

function runDagreLayout(
  pipelines: PipelineDefinition[],
  sharedNodes: PipelineNode[],
) {
  const g = new dagre.graphlib.Graph({ compound: true });
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  for (const node of sharedNodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const pipeline of pipelines) {
    g.setNode(pipeline.id, {});
    for (const node of pipeline.nodes) {
      g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
      g.setParent(node.id, pipeline.id);
    }
    for (const edge of pipeline.edges) {
      g.setEdge(edge.source, edge.target);
    }
  }

  dagre.layout(g);

  // Dagre returns center coordinates. Convert to top-left.
  const pipelineIds = new Set(pipelines.map((p) => p.id));
  const positions = new Map<string, { x: number; y: number }>();
  for (const nodeId of g.nodes()) {
    if (pipelineIds.has(nodeId)) {
      continue;
    }
    const n = g.node(nodeId);
    positions.set(nodeId, {
      x: n.x - NODE_WIDTH / 2,
      y: n.y - NODE_HEIGHT / 2,
    });
  }
  return positions;
}

function buildPipelineGroup(
  pipeline: PipelineDefinition,
  absPositions: Map<string, { x: number; y: number }>,
) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const node of pipeline.nodes) {
    const pos = getPosition(absPositions, node.id);
    minX = Math.min(minX, pos.x);
    minY = Math.min(minY, pos.y);
    maxX = Math.max(maxX, pos.x);
    maxY = Math.max(maxY, pos.y);
  }

  const groupWidth = maxX - minX + NODE_WIDTH + GROUP_PADDING * 2;
  const groupHeight =
    maxY - minY + NODE_HEIGHT + GROUP_PADDING * 2 + GROUP_LABEL_HEIGHT;
  const groupId = `${pipeline.id}-group`;

  const groupNode: Node = {
    id: groupId,
    type: "pipelineGroup",
    position: {
      x: minX - GROUP_PADDING,
      y: minY - GROUP_PADDING - GROUP_LABEL_HEIGHT,
    },
    data: { label: pipeline.name },
    selectable: false,
    draggable: false,
    style: { width: groupWidth, height: groupHeight },
  };

  const childNodes: Node[] = pipeline.nodes.map((node) => {
    const pos = getPosition(absPositions, node.id);
    return {
      id: node.id,
      type: "pipeline",
      parentId: groupId,
      extent: "parent" as const,
      position: {
        x: pos.x - minX + GROUP_PADDING,
        y: pos.y - minY + GROUP_PADDING + GROUP_LABEL_HEIGHT,
      },
      data: { ...node, detailStatus: resolveDetailStatus(node) },
    };
  });

  return { groupNode, childNodes };
}

function toFlowNode(
  node: PipelineNode,
  position: { x: number; y: number },
): Node {
  return {
    id: node.id,
    type: "pipeline",
    position,
    data: { ...node, detailStatus: resolveDetailStatus(node) },
  };
}
