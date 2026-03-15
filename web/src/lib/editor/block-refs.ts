export interface BlockRefMatch {
  from: number;
  to: number;
  query: string;
}

export function findBlockRefMatch(textBeforeCursor: string, blockStartPos: number): BlockRefMatch | null {
  const lastOpen = textBeforeCursor.lastIndexOf("((");
  if (lastOpen < 0) {
    return null;
  }
  const closerAfterOpen = textBeforeCursor.indexOf("))", lastOpen);
  if (closerAfterOpen >= 0) {
    return null;
  }
  const query = textBeforeCursor.slice(lastOpen + 2);
  return {
    from: blockStartPos + lastOpen,
    to: blockStartPos + textBeforeCursor.length,
    query,
  };
}

export function normalizeBlockRefToken(value: string): string {
  let normalized = value.trim();
  if (normalized.startsWith("((")) {
    normalized = normalized.slice(2);
  }
  if (normalized.endsWith("))")) {
    normalized = normalized.slice(0, -2);
  }
  return normalized.trim();
}

export function toBlockRefToken(blockUid: string): string {
  return `((${normalizeBlockRefToken(blockUid)}))`;
}
