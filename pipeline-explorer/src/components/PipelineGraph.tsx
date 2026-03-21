"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type NodeTypes,
  type NodeMouseHandler,
} from "@xyflow/react";
import dagre from "@dagrejs/dagre";
import "@xyflow/react/dist/style.css";

import type { PipelineDefinition, PipelineNode } from "@/types/pipeline";
import { getNodeContent } from "@/pipelines/node-content";
import { PipelineNodeComponent } from "./PipelineNode";
import { PipelineGroupNode } from "./PipelineGroupNode";
import { NodeDetailPanel } from "./NodeDetailPanel";
import { NodeSelectionProvider } from "./NodeSelectionContext";

interface PipelineGraphProps {
  pipelines: PipelineDefinition[];
  sharedNodes: PipelineNode[];
}

const nodeTypes: NodeTypes = {
  pipeline: PipelineNodeComponent,
  pipelineGroup: PipelineGroupNode,
};

/** Estimated node dimensions for dagre layout */
const NODE_WIDTH = 220;
const NODE_HEIGHT = 60;
/** Padding inside the group box around the outermost nodes */
const GROUP_PADDING = 30;
/** Space reserved at top of group for the label */
const GROUP_LABEL_HEIGHT = 36;

/**
 * Build the full graph from all pipelines + shared nodes.
 *
 * 1. Feed every node and edge into a single dagre layout
 * 2. Compute group boxes from each pipeline's owned-node positions
 * 3. Convert owned nodes to relative positions inside their group
 * 4. Shared nodes stay at absolute positions (no group parent)
 */
function buildNodesAndEdges(
  pipelines: PipelineDefinition[],
  sharedNodes: PipelineNode[],
) {
  // --- Step 1: Run dagre on the full graph ---
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  // Add shared nodes
  for (const node of sharedNodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  // Add all pipeline-owned nodes and edges
  for (const pipeline of pipelines) {
    for (const node of pipeline.nodes) {
      g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    }
    for (const edge of pipeline.edges) {
      g.setEdge(edge.source, edge.target);
    }
  }

  dagre.layout(g);

  // Read back absolute positions (dagre returns center → convert to top-left)
  const absPositions = new Map<string, { x: number; y: number }>();
  for (const nodeId of g.nodes()) {
    const n = g.node(nodeId);
    absPositions.set(nodeId, { x: n.x - NODE_WIDTH / 2, y: n.y - NODE_HEIGHT / 2 });
  }

  // --- Step 2: Build React Flow nodes ---
  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];

  // Build a lookup from node ID → PipelineNode data (for label, type, url)
  const nodeDataMap = new Map<string, PipelineNode>();
  for (const node of sharedNodes) nodeDataMap.set(node.id, node);
  for (const pipeline of pipelines) {
    for (const node of pipeline.nodes) nodeDataMap.set(node.id, node);
  }

  // Create group nodes per pipeline, then add owned nodes as children
  for (const pipeline of pipelines) {
    // Compute bounding box of this pipeline's owned nodes
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    for (const node of pipeline.nodes) {
      const pos = absPositions.get(node.id)!;
      minX = Math.min(minX, pos.x);
      minY = Math.min(minY, pos.y);
      maxX = Math.max(maxX, pos.x);
      maxY = Math.max(maxY, pos.y);
    }

    const groupWidth = maxX - minX + NODE_WIDTH + GROUP_PADDING * 2;
    const groupHeight =
      maxY - minY + NODE_HEIGHT + GROUP_PADDING * 2 + GROUP_LABEL_HEIGHT;
    const groupId = `${pipeline.id}-group`;

    // Group node — must appear before its children
    allNodes.push({
      id: groupId,
      type: "pipelineGroup",
      position: { x: minX - GROUP_PADDING, y: minY - GROUP_PADDING - GROUP_LABEL_HEIGHT },
      data: { label: pipeline.name },
      selectable: false,
      draggable: false,
      style: { width: groupWidth, height: groupHeight },
    });

    // Owned nodes — relative to group
    for (const node of pipeline.nodes) {
      const pos = absPositions.get(node.id)!;
      allNodes.push({
        id: node.id,
        type: "pipeline",
        parentId: groupId,
        extent: "parent" as const,
        position: {
          x: pos.x - minX + GROUP_PADDING,
          y: pos.y - minY + GROUP_PADDING + GROUP_LABEL_HEIGHT,
        },
        data: {
          label: node.label,
          nodeType: node.type,
          url: node.url,
        },
      });
    }
  }

  // Shared nodes — absolute positions, no group parent
  for (const node of sharedNodes) {
    const pos = absPositions.get(node.id)!;
    allNodes.push({
      id: node.id,
      type: "pipeline",
      position: pos,
      data: {
        label: node.label,
        nodeType: node.type,
        url: node.url,
      },
    });
  }

  // --- Step 3: Build edges ---
  for (const pipeline of pipelines) {
    for (const edge of pipeline.edges) {
      allEdges.push({
        id: `${pipeline.id}-${edge.source}-${edge.target}`,
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

interface SelectedNode {
  id: string;
  label: string;
  nodeType: string;
}

function findNode(
  nodeId: string,
  pipelines: PipelineDefinition[],
  sharedNodes: PipelineNode[],
): SelectedNode | null {
  for (const node of sharedNodes) {
    if (node.id === nodeId) return { id: node.id, label: node.label, nodeType: node.type };
  }
  for (const p of pipelines) {
    const node = p.nodes.find((n) => n.id === nodeId);
    if (node) return { id: node.id, label: node.label, nodeType: node.type };
  }
  return null;
}

function updateUrl(node: SelectedNode | null) {
  const url = node
    ? `${window.location.pathname}?node=${node.id}`
    : window.location.pathname;
  window.history.replaceState({}, "", url);
}

export function PipelineGraph({ pipelines, sharedNodes }: PipelineGraphProps) {
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(() => {
    const nodeId = new URLSearchParams(window.location.search).get("node");
    if (!nodeId) return null;
    return findNode(nodeId, pipelines, sharedNodes);
  });

  const { allNodes, allEdges } = useMemo(
    () => buildNodesAndEdges(pipelines, sharedNodes),
    [pipelines, sharedNodes],
  );

  const selectNodeById = useCallback(
    (nodeId: string) => {
      const found = findNode(nodeId, pipelines, sharedNodes);
      if (found) {
        setSelectedNode(found);
        updateUrl(found);
      }
    },
    [pipelines, sharedNodes],
  );

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      if (node.id.endsWith("-group")) return;
      selectNodeById(node.id);
    },
    [selectNodeById],
  );

  const handleClosePanel = useCallback(() => {
    setSelectedNode(null);
    updateUrl(null);
  }, []);

  return (
    <NodeSelectionProvider value={selectNodeById}>
      <div className="w-full h-full relative">
        <ReactFlow
          nodes={allNodes}
          edges={allEdges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.2}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} size={1} />
          <Controls />
        </ReactFlow>

        {selectedNode && (
          <NodeDetailPanel
            nodeId={selectedNode.id}
            nodeLabel={selectedNode.label}
            nodeType={selectedNode.nodeType}
            content={getNodeContent(selectedNode.id)}
            onClose={handleClosePanel}
          />
        )}
      </div>
    </NodeSelectionProvider>
  );
}
