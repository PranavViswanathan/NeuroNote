type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  return value as JsonRecord;
}

function getChildren(node: JsonRecord): JsonRecord[] {
  const content = node.content;
  if (!Array.isArray(content)) {
    return [];
  }
  return content
    .map((item) => asRecord(item))
    .filter((item): item is JsonRecord => item !== null);
}

function extractNodeLines(node: JsonRecord): string[] {
  if (node.type === "text" && typeof node.text === "string") {
    return [node.text];
  }

  if (node.type === "mathInline" || node.type === "mathBlock") {
    const attrs = asRecord(node.attrs);
    const latex = attrs && typeof attrs.latex === "string" ? attrs.latex.trim() : "";
    return latex ? [`[math:${latex}]`] : [];
  }

  if (node.type === "image") {
    const attrs = asRecord(node.attrs);
    const alt = attrs && typeof attrs.alt === "string" ? attrs.alt.trim() : "";
    return alt ? [`[image:${alt}]`] : ["[image]"];
  }

  const children = getChildren(node);
  if (children.length === 0) {
    return [];
  }

  if (node.type === "paragraph" || node.type === "heading" || node.type === "listItem") {
    const line = children.flatMap(extractNodeLines).join("").trim();
    return line.length > 0 ? [line] : [];
  }

  return children.flatMap(extractNodeLines);
}

export function extractPlainText(doc: Record<string, unknown>): string {
  const node = asRecord(doc);
  if (node === null) {
    return "";
  }
  return extractNodeLines(node).join("\n");
}
