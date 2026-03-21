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
import { NodeDetailPanel } from "./NodeDetailPanel";
import { NodeSelectionProvider } from "./NodeSelectionContext";

interface PipelineGraphProps {
  pipelines: PipelineDefinition[];
}

const nodeTypes: NodeTypes = {
  pipeline: PipelineNodeComponent,
};

/** Horizontal spacing between pipeline groups */
const PIPELINE_GAP = 400;

/**
 * Lay out all pipelines side by side on a single canvas.
 * Each pipeline's node positions are offset so the groups don't overlap.
 */
function buildNodesAndEdges(pipelines: PipelineDefinition[]) {
  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];
  let xOffset = 0;

  for (const pipeline of pipelines) {
    // Find the width of this pipeline group so we can space them
    const maxX = Math.max(...pipeline.nodes.map((n) => n.position.x), 0);

    // Add a group label as a non-interactive node
    allNodes.push({
      id: `${pipeline.id}-label`,
      type: "default",
      position: { x: xOffset, y: -80 },
      data: { label: pipeline.name },
      selectable: false,
      draggable: false,
      style: {
        background: "transparent",
        border: "none",
        fontSize: "16px",
        fontWeight: 700,
        color: "#6b7280",
        width: "auto",
      },
    });

    for (const node of pipeline.nodes) {
      allNodes.push({
        id: node.id,
        type: "pipeline",
        position: {
          x: node.position.x + xOffset,
          y: node.position.y,
        },
        data: {
          label: node.label,
          nodeType: node.type,
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

    xOffset += maxX + PIPELINE_GAP;
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
      if (node.id.endsWith("-label")) return;
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
