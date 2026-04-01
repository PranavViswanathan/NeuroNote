"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import type { GlobalGraphResponse } from "../../../../shared/contracts/ts/v1/graph";
import { SkeletonGraph } from "../ui/Skeleton";
import { EmptyState } from "../ui/EmptyState";
import { ErrorMessage } from "../ui/ErrorMessage";

export interface GlobalGraphFilterState {
  min_confidence: number;
  include_types: string[];
}

interface GlobalGraphPanelProps {
  graph: GlobalGraphResponse | null;
  filters: GlobalGraphFilterState;
  isLoading: boolean;
  errorMessage: string | null;
  onRetry: () => void;
  onFiltersChange: (next: GlobalGraphFilterState) => void;
  onOpenNote: (noteId: string) => void;
}

function pickNodeColor(nodeType: string): string {
  if (nodeType === "note") {
    return "#1d6d4f";
  }
  if (nodeType === "entity") {
    return "#4568a6";
  }
  return "#6c6f75";
}

const GRAPH_HEIGHT = 320;

export function GlobalGraphPanel({
  graph,
  filters,
  isLoading,
  errorMessage,
  onRetry,
  onFiltersChange,
  onOpenNote,
}: GlobalGraphPanelProps) {
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const [rendererError, setRendererError] = useState<string | null>(null);
  const [rendererMode, setRendererMode] = useState<"sigma" | "fallback">("sigma");

  const viewModel = useMemo(
    () =>
      graph
        ? { nodes: graph.nodes, edges: graph.edges }
        : { nodes: [], edges: [] },
    [graph],
  );

  useEffect(() => {
    if (!canvasRef.current || viewModel.nodes.length === 0) {
      return;
    }

    let cancelled = false;
    let sigmaInstance: any = null;

    const renderCanvas = async () => {
      const hasWebGl2 =
        typeof window !== "undefined" &&
        typeof (window as Window & { WebGL2RenderingContext?: unknown }).WebGL2RenderingContext !==
          "undefined";
      if (!hasWebGl2) {
        if (!cancelled) {
          setRendererMode("fallback");
          setRendererError(null);
        }
        return;
      }

      try {
        setRendererError(null);
        setRendererMode("sigma");
        const [{ default: Sigma }, graphologyModule] = await Promise.all([
          import("sigma"),
          import("graphology"),
        ]);
        const Graph = graphologyModule.default;
        const graphology = new Graph();
        for (const node of viewModel.nodes) {
          graphology.addNode(node.id, {
            label: node.label,
            size: 8,
            color: pickNodeColor(node.type),
          });
        }
        for (const edge of viewModel.edges) {
          if (!graphology.hasNode(edge.source) || !graphology.hasNode(edge.target)) {
            continue;
          }
          graphology.addEdgeWithKey(edge.id, edge.source, edge.target, {
            label: edge.type,
            size: 1.2,
            color: "#8ba296",
          });
        }

        if (cancelled || !canvasRef.current) {
          return;
        }
        sigmaInstance = new Sigma(graphology, canvasRef.current);
        sigmaInstance.on("clickNode", ({ node }: { node: string }) => {
          const selected = viewModel.nodes.find((item) => item.id === node);
          if (selected?.type === "note") {
            onOpenNote(String(selected.metadata.note_id ?? selected.id));
          }
        });
      } catch {
        if (!cancelled) {
          setRendererMode("fallback");
          setRendererError(null);
        }
      }
    };

    void renderCanvas();

    return () => {
      cancelled = true;
      sigmaInstance?.kill();
    };
  }, [onOpenNote, viewModel.edges, viewModel.nodes]);

  const handleIncludeTypeToggle = (value: string, checked: boolean) => {
    const current = new Set(filters.include_types);
    if (checked) {
      current.add(value);
    } else {
      current.delete(value);
    }
    if (current.size === 0) {
      return;
    }
    onFiltersChange({
      ...filters,
      include_types: Array.from(current),
    });
  };

  const nodeCount = viewModel.nodes.length;
  const edgeCount = viewModel.edges.length;

  const fallbackPositions = useMemo(() => {
    const centerX = 50;
    const centerY = 50;
    const radius = 34;
    const count = Math.max(viewModel.nodes.length, 1);
    const map = new Map<string, { x: number; y: number }>();

    viewModel.nodes.forEach((node, index) => {
      const angle = (index / count) * Math.PI * 2;
      map.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });
    return map;
  }, [viewModel.nodes]);

  if (isLoading) {
    return <SkeletonGraph />;
  }

  if (errorMessage) {
    return (
      <ErrorMessage
        message={errorMessage}
        actionLabel="Retry"
        onAction={onRetry}
      />
    );
  }

  return (
    <section className="local-graph-panel" aria-label="Global graph panel">
      <header className="local-graph-header">
        <h2>Global graph</h2>
      </header>

      <div className="local-graph-filters">
        <label>
          Min confidence
          <input
            aria-label="Minimum confidence"
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={filters.min_confidence}
            onChange={(event) => {
              onFiltersChange({
                ...filters,
                min_confidence: Number(event.target.value),
              });
            }}
          />
        </label>

        <fieldset className="local-graph-type-filters">
          <legend>Include</legend>
          {["note", "entity", "relation"].map((item) => (
            <label key={item}>
              <input
                type="checkbox"
                aria-label={`Include ${item}`}
                checked={filters.include_types.includes(item)}
                onChange={(event) => {
                  handleIncludeTypeToggle(item, event.target.checked);
                }}
              />
              {item}
            </label>
          ))}
        </fieldset>
      </div>

      <div className="local-graph-summary">
        <p>{nodeCount} nodes</p>
        <p>{edgeCount} edges</p>
      </div>

      {nodeCount === 0 ? (
        <EmptyState
          icon="🕸️"
          title="No notes yet"
          description="Start creating notes to see your knowledge graph."
        />
      ) : null}

      {rendererMode === "sigma" ? (
        <div
          ref={canvasRef}
          className="local-graph-canvas-placeholder"
          aria-label="Global graph canvas"
          style={{ height: `${GRAPH_HEIGHT}px` }}
        />
      ) : (
        <svg
          className="local-graph-canvas-placeholder local-graph-canvas-fallback"
          aria-label="Global graph canvas"
          viewBox="0 0 100 100"
          role="img"
          style={{ height: `${GRAPH_HEIGHT}px` }}
        >
          {viewModel.edges.map((edge) => {
            const source = fallbackPositions.get(edge.source);
            const target = fallbackPositions.get(edge.target);
            if (!source || !target) {
              return null;
            }
            return (
              <line
                key={edge.id}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="#8ba296"
                strokeWidth="1.2"
              />
            );
          })}
          {viewModel.nodes.map((node) => {
            const position = fallbackPositions.get(node.id);
            if (!position) {
              return null;
            }
            return (
              <g
                key={node.id}
                onClick={() => {
                  if (node.type === "note") {
                    onOpenNote(String(node.metadata.note_id ?? node.id));
                  }
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    if (node.type === "note") {
                      onOpenNote(String(node.metadata.note_id ?? node.id));
                    }
                  }
                }}
              >
                <circle
                  cx={position.x}
                  cy={position.y}
                  r={3.4}
                  fill={pickNodeColor(node.type)}
                  stroke="#fff"
                  strokeWidth={0.8}
                />
              </g>
            );
          })}
        </svg>
      )}

      {rendererError ? <ErrorMessage message={rendererError} compact /> : null}

      <ul className="local-graph-node-list" role="listbox" aria-label="Global graph nodes">
        {viewModel.nodes.map((node) => (
          <li key={node.id}>
            <button
              type="button"
              className="local-graph-node-button"
              onClick={() => {
                if (node.type === "note") {
                  onOpenNote(String(node.metadata.note_id ?? node.id));
                }
              }}
            >
              <span>{node.label}</span>
              <span>{node.type}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
