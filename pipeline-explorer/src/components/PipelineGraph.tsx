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

import type { PipelineDefinition } from "@/types/pipeline";
import { getNodeContent } from "@/pipelines/node-content";
import { PipelineNodeComponent } from "./PipelineNode";
import { PipelineGroupNode } from "./PipelineGroupNode";
import { NodeDetailPanel } from "./NodeDetailPanel";
import { NodeSelectionProvider } from "./NodeSelectionContext";

interface PipelineGraphProps {
  pipelines: PipelineDefinition[];
}

const nodeTypes: NodeTypes = {
  pipeline: PipelineNodeComponent,
  pipelineGroup: PipelineGroupNode,
};

/** Estimated node dimensions for dagre layout */
const NODE_WIDTH = 220;
const NODE_HEIGHT = 60;
/** Spacing between pipeline groups */
const PIPELINE_GAP = 100;
/** Padding inside the group box around the outermost nodes */
const GROUP_PADDING = 30;
/** Space reserved at top of group for the label */
const GROUP_LABEL_HEIGHT = 36;

/**
 * Use dagre to compute positions for a single pipeline's nodes,
 * then wrap them in a React Flow group node.
 */
function layoutPipeline(pipeline: PipelineDefinition) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  for (const node of pipeline.nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const edge of pipeline.edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  // Dagre returns center coordinates — convert to top-left
  const positions = new Map<string, { x: number; y: number }>();
  for (const node of pipeline.nodes) {
    const dagreNode = g.node(node.id);
    positions.set(node.id, {
      x: dagreNode.x - NODE_WIDTH / 2,
      y: dagreNode.y - NODE_HEIGHT / 2,
    });
  }

  return positions;
}

/**
 * Lay out all pipelines side by side on a single canvas.
 * Each pipeline becomes a React Flow group node with dagre-computed
 * child positions.
 */
function buildNodesAndEdges(pipelines: PipelineDefinition[]) {
  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];
  let xOffset = 0;

  for (const pipeline of pipelines) {
    const positions = layoutPipeline(pipeline);

    // Compute bounding box of laid-out nodes
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    for (const pos of positions.values()) {
      minX = Math.min(minX, pos.x);
      minY = Math.min(minY, pos.y);
      maxX = Math.max(maxX, pos.x);
      maxY = Math.max(maxY, pos.y);
    }

    const groupWidth = maxX - minX + NODE_WIDTH + GROUP_PADDING * 2;
    const groupHeight =
      maxY - minY + NODE_HEIGHT + GROUP_PADDING * 2 + GROUP_LABEL_HEIGHT;

    const groupId = `${pipeline.id}-group`;

    // Group node — must appear before its children in the array
    allNodes.push({
      id: groupId,
      type: "pipelineGroup",
      position: { x: xOffset, y: 0 },
      data: { label: pipeline.name },
      selectable: false,
      draggable: false,
      style: { width: groupWidth, height: groupHeight },
    });

    for (const node of pipeline.nodes) {
      const pos = positions.get(node.id)!;
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

    xOffset += groupWidth + PIPELINE_GAP;
  }

  return { allNodes, allEdges };
}

interface SelectedNode {
  id: string;
  label: string;
  nodeType: string;
}

function findNodeInPipelines(
  nodeId: string,
  pipelines: PipelineDefinition[],
): SelectedNode | null {
  for (const p of pipelines) {
    const node = p.nodes.find((n) => n.id === nodeId);
    if (node) return { id: node.id, label: node.label, nodeType: node.type };
  }
  return null;
}

function getInitialNode(
  pipelines: PipelineDefinition[],
): SelectedNode | null {
  const nodeId = new URLSearchParams(window.location.search).get("node");
  if (!nodeId) return null;
  return findNodeInPipelines(nodeId, pipelines);
}

function updateUrl(node: SelectedNode | null) {
  const url = node
    ? `${window.location.pathname}?node=${node.id}`
    : window.location.pathname;
  window.history.replaceState({}, "", url);
}

export function PipelineGraph({ pipelines }: PipelineGraphProps) {
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(() =>
    getInitialNode(pipelines),
  );

  const { allNodes, allEdges } = useMemo(
    () => buildNodesAndEdges(pipelines),
    [pipelines],
  );

  const selectNodeById = useCallback(
    (nodeId: string) => {
      const found = findNodeInPipelines(nodeId, pipelines);
      if (found) {
        setSelectedNode(found);
        updateUrl(found);
      }
    },
    [pipelines],
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
