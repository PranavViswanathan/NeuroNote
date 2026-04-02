import type { LocalGraphResponse } from "../../../../shared/contracts/ts/v1/graph";
import type { LocalGraphViewModel } from "./types";

export function toLocalGraphViewModel(payload: LocalGraphResponse): LocalGraphViewModel {
  return {
    nodes: payload.nodes,
    edges: payload.edges,
  };
}
