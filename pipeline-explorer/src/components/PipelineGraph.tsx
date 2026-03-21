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

/** Horizontal spacing between pipeline groups */
const PIPELINE_GAP = 100;
/** Estimated node dimensions for bounding-box calculation */
const NODE_WIDTH = 220;
const NODE_HEIGHT = 60;
/** Padding inside the group box around the outermost nodes */
const GROUP_PADDING = 30;
/** Space reserved at top of group for the label */
const GROUP_LABEL_HEIGHT = 36;

/**
 * Lay out all pipelines side by side on a single canvas.
 * Each pipeline becomes a React Flow group node, with children
 * positioned relative to it.
 */
function buildNodesAndEdges(pipelines: PipelineDefinition[]) {
  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];
  let xOffset = 0;

  for (const pipeline of pipelines) {
    const xs = pipeline.nodes.map((n) => n.position.x);
    const ys = pipeline.nodes.map((n) => n.position.y);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);

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
      allNodes.push({
        id: node.id,
        type: "pipeline",
        parentId: groupId,
        extent: "parent" as const,
        position: {
          x: node.position.x - minX + GROUP_PADDING,
          y: node.position.y - minY + GROUP_PADDING + GROUP_LABEL_HEIGHT,
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
