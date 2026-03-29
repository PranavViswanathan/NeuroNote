import type { LocalGraphEdge, LocalGraphNode } from "../../../../shared/contracts/ts/v1/graph";

export interface LocalGraphViewModel {
  nodes: LocalGraphNode[];
  edges: LocalGraphEdge[];
}
