"use client";

import { useState } from "react";

import { D3GraphCanvas } from "./D3GraphCanvas";
import type { LocalGraphResponse } from "../../../../shared/contracts/ts/v1/graph";
import { SkeletonGraph } from "../ui/Skeleton";
import { EmptyState } from "../ui/EmptyState";
import { ErrorMessage } from "../ui/ErrorMessage";

interface LocalGraphPanelProps {
  noteId: string;
  graph: LocalGraphResponse | null;
  filters: {
    max_hops: number;
    limit_nodes: number;
    min_confidence: number;
    include_types: string[];
  };
  isLoading: boolean;
  errorMessage: string | null;
  onRetry: () => void;
  onFiltersChange: (next: {
    max_hops: number;
    limit_nodes: number;
    min_confidence: number;
    include_types: string[];
  }) => void;
  onOpenNote: (noteId: string) => void;
}

export function LocalGraphPanel({
  noteId,
  graph,
  filters,
  isLoading,
  errorMessage,
  onRetry,
  onFiltersChange,
  onOpenNote,
}: LocalGraphPanelProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

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

  const nodeCount = graph?.nodes.length ?? 0;
  const edgeCount = graph?.edges.length ?? 0;

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
    <section className="local-graph-panel" aria-label="Local graph panel">
      <header className="local-graph-header">
        <h2>Local graph</h2>
      </header>

      <div className="local-graph-filters">
        <label>
          Depth
          <select
            aria-label="Graph depth"
            value={filters.max_hops}
            onChange={(event) => {
              onFiltersChange({
                ...filters,
                max_hops: Number(event.target.value),
              });
            }}
          >
            <option value={1}>1 hop</option>
            <option value={2}>2 hops</option>
          </select>
        </label>

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

      {graph !== null && (
        <>
          {nodeCount === 0 ? (
            <EmptyState
              icon="🕸️"
              title="No connections yet"
              description="Add wiki links or process this note to discover relationships."
            />
          ) : (
            <D3GraphCanvas
              nodes={graph.nodes}
              edges={graph.edges}
              rootNodeId={noteId}
              height={300}
              ariaLabel="Local graph canvas"
              onNodeClick={(node) => {
                setSelectedNodeId(node.id);
                if (node.type === "note") {
                  onOpenNote(String(node.metadata.note_id ?? node.id));
                }
              }}
            />
          )}

          <ul className="local-graph-node-list" role="listbox" aria-label="Local graph nodes">
            {graph.nodes.map((node) => (
              <li key={node.id}>
                <button
                  type="button"
                  className={`local-graph-node-button${selectedNodeId === node.id ? " selected" : ""}`}
                  onClick={() => {
                    setSelectedNodeId(node.id);
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
        </>
      )}
    </section>
  );
}
