export interface WikiLinkMatch {
  from: number;
  to: number;
  query: string;
}

export function findWikiLinkMatch(textBeforeCursor: string, blockStartPos: number): WikiLinkMatch | null {
  const lastOpen = textBeforeCursor.lastIndexOf("[[");
  if (lastOpen < 0) {
    return null;
  }
  const closerAfterOpen = textBeforeCursor.indexOf("]]", lastOpen);
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

export function normalizeWikiLinkTitle(value: string): string {
  let normalized = value.trim();
  if (normalized.startsWith("[[")) {
    normalized = normalized.slice(2);
  }
  if (normalized.endsWith("]]")) {
    normalized = normalized.slice(0, -2);
  }
  return normalized.replace(/\s+/g, " ").trim();
}
