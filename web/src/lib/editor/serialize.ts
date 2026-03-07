export interface EditorDoc extends Record<string, unknown> {
  type: "doc";
  content: EditorNode[];
}

type EditorNode = Record<string, unknown>;

export function createEmptyEditorDoc(): EditorDoc {
  return { type: "doc", content: [] };
}

function isEditorDoc(value: unknown): value is EditorDoc {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const asRecord = value as Record<string, unknown>;
  return asRecord.type === "doc" && Array.isArray(asRecord.content);
}

export function coerceEditorDoc(value: unknown): EditorDoc {
  if (!isEditorDoc(value)) {
    return createEmptyEditorDoc();
  }
  return value;
}

export function serializeEditorDoc(value: Record<string, unknown>): string {
  return JSON.stringify(value);
}

export function deserializeEditorDoc(value: string): EditorDoc {
  try {
    const parsed = JSON.parse(value) as unknown;
    return coerceEditorDoc(parsed);
  } catch {
    return createEmptyEditorDoc();
  }
}
