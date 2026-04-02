"use client";

import { useEffect, useRef, useState } from "react";

import { D3GraphCanvas } from "./D3GraphCanvas";
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

export function GlobalGraphPanel({
  graph,
  filters,
  isLoading,
  errorMessage,
  onRetry,
  onFiltersChange,
  onOpenNote,
}: GlobalGraphPanelProps) {
  const [nodeSearch, setNodeSearch] = useState("");
  const [canvasHeight, setCanvasHeight] = useState(600);
  const canvasAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = canvasAreaRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const h = entries[0]?.contentRect.height;
      if (h && h > 0) setCanvasHeight(h);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const normalizedSearch = nodeSearch.trim().toLowerCase();

  const visibleNodes = graph
    ? normalizedSearch
      ? graph.nodes.filter((n) => n.label.toLowerCase().includes(normalizedSearch))
      : graph.nodes
    : [];

  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

  const visibleEdges = graph
    ? graph.edges.filter(
        (e) => visibleNodeIds.has(String(e.source)) && visibleNodeIds.has(String(e.target)),
      )
    : [];

  const nodeCount = visibleNodes.length;
  const edgeCount = visibleEdges.length;

  return (
    <div className="global-graph-view" aria-label="Global graph view">
      <aside className="global-graph-sidebar">
        <h2>Knowledge Graph</h2>
        <input
          className="notes-filter-input"
          type="text"
          aria-label="Search nodes"
          placeholder="Search nodes…"
          value={nodeSearch}
          onChange={(e) => setNodeSearch(e.target.value)}
        />
        <div className="local-graph-summary">
          <p>{nodeCount} nodes</p>
          <p>{edgeCount} edges</p>
        </div>
        {graph?.meta.truncated && (
          <p className="global-graph-truncated-note">
            Showing top {graph.meta.applied_filters.limit_nodes} nodes
          </p>
        )}
        <div className="local-graph-filters">
          <label>
            Min confidence
            <input
              aria-label="Minimum confidence"
              type="range" min={0} max={1} step={0.05}
              value={filters.min_confidence}
              onChange={(e) => onFiltersChange({ ...filters, min_confidence: Number(e.target.value) })}
            />
            <span>{filters.min_confidence.toFixed(2)}</span>
          </label>
          <fieldset className="local-graph-type-filters">
            <legend>Include</legend>
            {["note", "entity", "relation"].map((item) => (
              <label key={item}>
                <input
                  type="checkbox"
                  aria-label={`Include ${item}`}
                  checked={filters.include_types.includes(item)}
                  onChange={(e) => {
                    const current = new Set(filters.include_types);
                    if (e.target.checked) current.add(item); else current.delete(item);
                    if (current.size === 0) return;
                    onFiltersChange({ ...filters, include_types: Array.from(current) });
                  }}
                />
                {item}
              </label>
            ))}
          </fieldset>
        </div>
      </aside>

      <div className="global-graph-canvas-area" ref={canvasAreaRef}>
        {isLoading ? (
          <SkeletonGraph />
        ) : errorMessage ? (
          <ErrorMessage
            message={errorMessage}
            actionLabel="Retry"
            onAction={onRetry}
          />
        ) : !graph || nodeCount === 0 ? (
          <EmptyState
            icon="🕸️"
            title={normalizedSearch ? "No matching nodes" : "No notes yet"}
            description={
              normalizedSearch
                ? "Try a different search term."
                : "Start creating notes to see your knowledge graph."
            }
          />
        ) : (
          <D3GraphCanvas
            nodes={visibleNodes}
            edges={visibleEdges}
            height={canvasHeight}
            onNodeClick={(node) => {
              if (node.type === "note") onOpenNote(String(node.metadata.note_id ?? node.id));
            }}
          />
        )}
      </div>
    </div>
  );
}
