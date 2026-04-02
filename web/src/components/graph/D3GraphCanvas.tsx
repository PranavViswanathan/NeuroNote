"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

import type { LocalGraphNode, LocalGraphEdge } from "../../../../shared/contracts/ts/v1/graph";

interface D3GraphCanvasProps {
  nodes: LocalGraphNode[];
  edges: LocalGraphEdge[];
  rootNodeId?: string;
  highlightNodeId?: string;
  onNodeClick: (node: LocalGraphNode) => void;
  width?: number;
  height: number;
  ariaLabel?: string;
}

const MAX_RENDER_NODES = 300;

type SimNode = LocalGraphNode & d3.SimulationNodeDatum;

type SimEdge = Omit<LocalGraphEdge, "source" | "target"> &
  d3.SimulationLinkDatum<SimNode>;

function pickNodeColor(type: string): string {
  if (type === "note") return "#1d6d4f";
  if (type === "entity") return "#4568a6";
  return "#6c6f75";
}

export function D3GraphCanvas({
  nodes,
  edges,
  rootNodeId,
  highlightNodeId,
  onNodeClick,
  width: widthProp,
  height,
  ariaLabel,
}: D3GraphCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  // Stable refs so the pan-to-highlight effect can access current sim state
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const simNodesRef = useRef<SimNode[]>([]);

  // Main effect: rebuild simulation whenever nodes/edges/dimensions change
  useEffect(() => {
    if (!svgRef.current) return;

    // Re-measure each time the effect runs — SVG is in the DOM by now
    const rect = svgRef.current.getBoundingClientRect();
    const width = widthProp ?? (rect.width > 0 ? rect.width : 800);

    // Cap node count to avoid pegging the CPU on very large graphs.
    // Retain the highest-connected nodes so the most relevant structure is visible.
    let renderNodes = nodes;
    let renderEdges = edges;
    if (nodes.length > MAX_RENDER_NODES) {
      const edgeDegree = new Map<string, number>();
      for (const e of edges) {
        edgeDegree.set(e.source, (edgeDegree.get(e.source) ?? 0) + 1);
        edgeDegree.set(e.target, (edgeDegree.get(e.target) ?? 0) + 1);
      }
      renderNodes = [...nodes]
        .sort((a, b) => (edgeDegree.get(b.id) ?? 0) - (edgeDegree.get(a.id) ?? 0))
        .slice(0, MAX_RENDER_NODES);
      const visibleIds = new Set(renderNodes.map((n) => n.id));
      renderEdges = edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target));
    }

    const simNodes: SimNode[] = renderNodes.map((n) => ({ ...n }));
    const simEdges: SimEdge[] = renderEdges.map((e) => ({ ...e }));
    simNodesRef.current = simNodes; // D3 mutates these in-place; ref stays current

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g").attr("class", "graph-root");

    const linkSelection = g
      .selectAll<SVGLineElement, SimEdge>("line")
      .data(simEdges)
      .enter()
      .append("line")
      .attr("stroke", "#8ba296")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.7);

    const nodeSelection = g
      .selectAll<SVGGElement, SimNode>("g.node")
      .data(simNodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .style("cursor", "pointer");

    nodeSelection.each(function (d) {
      const isRoot = rootNodeId === d.id;
      const isHighlight = highlightNodeId === d.id;
      const radius = isHighlight ? 14 : isRoot ? 12 : 8;

      d3.select(this)
        .append("circle")
        .attr("r", radius)
        .attr("fill", isHighlight ? "#e07b1a" : pickNodeColor(d.type))
        .attr("stroke", isHighlight ? "#b85e10" : isRoot ? "#0f4e39" : "#fff")
        .attr("stroke-width", isHighlight ? 3 : isRoot ? 2 : 1);

      d3.select(this)
        .append("text")
        .attr("dy", "0.35em")
        .attr("x", radius + 4)
        .attr("font-size", isHighlight ? "11" : "10")
        .attr("font-weight", isHighlight ? "600" : "normal")
        .attr("fill", isHighlight ? "#7a3d0a" : "#6c6f75")
        .attr("pointer-events", "none")
        .text(d.label.length > 24 ? d.label.slice(0, 24) : d.label);
    });

    nodeSelection.on("click", (_event, d) => {
      const original = nodes.find((n) => n.id === d.id);
      if (original) onNodeClick(original);
    });

    // Cool the simulation faster when there are many nodes to avoid long CPU spikes.
    // Default alphaDecay ≈ 0.0228 (~300 ticks); scale up for larger graphs.
    const alphaDecay = simNodes.length > 150 ? 0.05 : 0.0228;

    const simulation = d3
      .forceSimulation<SimNode>(simNodes)
      .alphaDecay(alphaDecay)
      .force(
        "link",
        d3.forceLink<SimNode, SimEdge>(simEdges).id((d) => d.id).distance(90),
      )
      .force("charge", d3.forceManyBody<SimNode>().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide<SimNode>(20));

    simulation.on("tick", () => {
      linkSelection
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);
      nodeSelection.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    const drag = d3
      .drag<SVGGElement, SimNode>()
      .on("start", (_event, d) => {
        simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (_event, d) => {
        simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    nodeSelection.call(drag);

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);
    zoomRef.current = zoom;

    // After simulation settles, zoom to fit all nodes in view.
    // Re-measure the SVG here so fitAll uses the actual rendered size.
    const fitAll = () => {
      if (simNodes.length === 0) return;
      const r = svgRef.current?.getBoundingClientRect();
      const w = r && r.width > 0 ? r.width : width;
      const h = r && r.height > 0 ? r.height : height;

      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (const n of simNodes) {
        const x = n.x ?? 0;
        const y = n.y ?? 0;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
      const PADDING = 48;
      const boxW = maxX - minX + PADDING * 2;
      const boxH = maxY - minY + PADDING * 2;
      const scale = Math.min(w / boxW, h / boxH, 1.5);
      const tx = w / 2 - scale * ((minX + maxX) / 2);
      const ty = h / 2 - scale * ((minY + maxY) / 2);
      svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
    };

    simulation.on("end", fitAll);

    return () => {
      simulation.stop();
      svg.on(".zoom", null);
    };
  }, [nodes, edges, rootNodeId, highlightNodeId, onNodeClick, widthProp, height]);

  // Pan to the highlighted node whenever it changes (without restarting simulation)
  useEffect(() => {
    if (!highlightNodeId || !svgRef.current || !zoomRef.current) return;
    const node = simNodesRef.current.find((n) => n.id === highlightNodeId);
    if (!node || node.x == null || node.y == null) return;

    const r = svgRef.current.getBoundingClientRect();
    const w = r.width > 0 ? r.width : 800;
    const h = r.height > 0 ? r.height : 600;
    const scale = 2;
    const tx = w / 2 - scale * node.x;
    const ty = h / 2 - scale * node.y;
    d3.select(svgRef.current)
      .transition()
      .duration(400)
      .call(zoomRef.current.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }, [highlightNodeId]);

  return (
    <svg
      ref={svgRef}
      width={widthProp ?? "100%"}
      height={height}
      aria-label={ariaLabel}
      style={{ cursor: "grab", display: "block", background: "transparent" }}
    />
  );
}
