"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  type NodeMouseHandler,
  type NodeTypes,
  ReactFlow,
} from "@xyflow/react";
import { useCallback, useMemo, useState } from "react";

import { buildNodesAndEdges, findNode, type SelectedNode } from "@/lib/layout";
import { getNodeContent } from "@/pipelines/node-content";
import type { PipelineDefinition, PipelineNode } from "@/types/pipeline";
import { NodeDetailPanel } from "./NodeDetailPanel";
import { NodeSelectionProvider } from "./NodeSelectionContext";
import { PipelineGroupNode } from "./PipelineGroupNode";
import { PipelineNodeComponent } from "./PipelineNode";

interface PipelineGraphProps {
  pipelines: PipelineDefinition[];
  sharedNodes: PipelineNode[];
}

const nodeTypes: NodeTypes = {
  pipeline: PipelineNodeComponent,
  pipelineGroup: PipelineGroupNode,
};

export function PipelineGraph({ pipelines, sharedNodes }: PipelineGraphProps) {
  const [selectedNode, setSelectedNode] = useState(() => {
    const nodeId = new URLSearchParams(window.location.search).get("node");
    if (!nodeId) {
      return null;
    }
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
      if (node.id.endsWith("-group")) {
        return;
      }
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
          <Background
            gap={24}
            size={1.5}
            variant={BackgroundVariant.Dots}
            color="#cbd5e1"
          />
          <Controls />
        </ReactFlow>

        {selectedNode && (
          <NodeDetailPanel
            nodeId={selectedNode.id}
            nodeLabel={selectedNode.label}
            nodeType={selectedNode.nodeType}
            verified={selectedNode.verified}
            content={getNodeContent(selectedNode.id)}
            onClose={handleClosePanel}
          />
        )}
      </div>
    </NodeSelectionProvider>
  );
}

export function updateUrl(node: SelectedNode | null) {
  const url = node
    ? `${window.location.pathname}?node=${node.id}`
    : window.location.pathname;
  window.history.replaceState({}, "", url);
}
