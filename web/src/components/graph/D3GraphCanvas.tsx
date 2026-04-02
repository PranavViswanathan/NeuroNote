"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

import type { LocalGraphNode, LocalGraphEdge } from "../../../../shared/contracts/ts/v1/graph";

interface D3GraphCanvasProps {
  nodes: LocalGraphNode[];
  edges: LocalGraphEdge[];
  rootNodeId?: string;
  onNodeClick: (node: LocalGraphNode) => void;
  height: number;
  ariaLabel?: string;
}

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
  onNodeClick,
  height,
  ariaLabel,
}: D3GraphCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const { width: svgWidth } = svgRef.current.getBoundingClientRect() ?? { width: 600 };
    const width = svgWidth || 600;

    const simNodes: SimNode[] = nodes.map((n) => ({ ...n, x: 0, y: 0, vx: 0, vy: 0 }));
    const simEdges: SimEdge[] = edges.map((e) => ({ ...e }));

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
      const radius = isRoot ? 12 : 8;

      d3.select(this)
        .append("circle")
        .attr("r", radius)
        .attr("fill", pickNodeColor(d.type))
        .attr("stroke", isRoot ? "#0f4e39" : "#fff")
        .attr("stroke-width", isRoot ? 2 : 1);

      d3.select(this)
        .append("text")
        .attr("dy", "0.35em")
        .attr("x", radius + 4)
        .attr("font-size", "10")
        .attr("fill", "#6c6f75")
        .attr("pointer-events", "none")
        .text(d.label.length > 20 ? d.label.slice(0, 20) : d.label);
    });

    nodeSelection.on("click", (_event, d) => {
      const original = nodes.find((n) => n.id === d.id);
      if (original) {
        onNodeClick(original);
      }
    });

    const simulation = d3
      .forceSimulation<SimNode>(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimEdge>(simEdges)
          .id((d) => d.id)
          .distance(90),
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

    const fitAll = () => {
      if (simNodes.length === 0) return;
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
      const scale = Math.min(width / boxW, height / boxH, 1.5);
      const tx = width / 2 - scale * ((minX + maxX) / 2);
      const ty = height / 2 - scale * ((minY + maxY) / 2);
      svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
    };

    simulation.on("end", fitAll);

    return () => {
      simulation.stop();
      svg.on(".zoom", null);
    };
  }, [nodes, edges, rootNodeId, onNodeClick, height]);

  return (
    <svg
      ref={svgRef}
      width="100%"
      height={height}
      aria-label={ariaLabel}
      style={{ cursor: "grab", display: "block", background: "transparent" }}
    />
  );
}
