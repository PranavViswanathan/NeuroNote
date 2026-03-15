import type { JSONContent } from "@tiptap/react";

interface BlockAttrs {
  blockUid?: string;
  parentBlockUid?: string | null;
  indentLevel?: number;
}

export interface HierarchyActions {
  canIndent: boolean;
  canOutdent: boolean;
  parentCandidateUid: string | null;
}

const NESTABLE_BLOCK_TYPES = new Set([
  "paragraph",
  "heading",
  "blockquote",
  "codeBlock",
  "horizontalRule",
  "bulletList",
  "orderedList",
  "taskList",
  "taskItem",
  "listItem",
  "mathBlock",
  "image",
]);

function cloneDoc(doc: JSONContent): JSONContent {
  return JSON.parse(JSON.stringify(doc)) as JSONContent;
}

function asAttrs(node: JSONContent | undefined): BlockAttrs {
  if (!node || typeof node !== "object" || !node.attrs || typeof node.attrs !== "object") {
    return {};
  }
  return node.attrs as BlockAttrs;
}

function extractNodeText(node: JSONContent | undefined): string {
  if (!node) {
    return "";
  }
  const parts: string[] = [];
  const walk = (value: JSONContent | JSONContent[] | undefined): void => {
    if (!value) {
      return;
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        walk(item);
      }
      return;
    }
    if (typeof value.text === "string") {
      parts.push(value.text);
    }
    if (Array.isArray(value.content)) {
      walk(value.content as JSONContent[]);
    }
  };
  walk(node);
  return parts.join(" ").replace(/\s+/g, " ").trim();
}

function ensureUid(node: JSONContent): string {
  if (!node.attrs || typeof node.attrs !== "object") {
    node.attrs = {};
  }
  const attrs = node.attrs as BlockAttrs;
  if (typeof attrs.blockUid === "string" && attrs.blockUid.trim()) {
    return attrs.blockUid;
  }
  const generated = `blk-${Date.now()}-${Math.floor(Math.random() * 10_000_000)}`;
  attrs.blockUid = generated;
  return generated;
}

function asTopLevelBlocks(doc: JSONContent): JSONContent[] {
  if (!Array.isArray(doc.content)) {
    return [];
  }
  return doc.content as JSONContent[];
}

function isNestable(node: JSONContent | undefined): boolean {
  return Boolean(node && typeof node.type === "string" && NESTABLE_BLOCK_TYPES.has(node.type));
}

function findBlockByUid(content: JSONContent[], uid: string | null | undefined): JSONContent | null {
  if (!uid) {
    return null;
  }
  for (const node of content) {
    const attrs = asAttrs(node);
    if (attrs.blockUid === uid) {
      return node;
    }
  }
  return null;
}

export function computeHierarchyActions(doc: JSONContent, blockIndex: number): HierarchyActions {
  const content = asTopLevelBlocks(doc);
  const current = content[blockIndex];
  const previous = content[blockIndex - 1];
  if (!isNestable(current)) {
    return { canIndent: false, canOutdent: false, parentCandidateUid: null };
  }
  const currentAttrs = asAttrs(current);
  return {
    canIndent: blockIndex > 0 && isNestable(previous),
    canOutdent: Boolean(currentAttrs.parentBlockUid),
    parentCandidateUid: isNestable(previous) ? (asAttrs(previous).blockUid ?? null) : null,
  };
}

export function resolveParentPreviewText(doc: JSONContent, blockIndex: number): string | null {
  const content = asTopLevelBlocks(doc);
  const previous = content[blockIndex - 1];
  if (!isNestable(previous)) {
    return null;
  }
  const text = extractNodeText(previous);
  if (!text) {
    return previous?.type ? `${previous.type} block` : "previous block";
  }
  if (text.length <= 44) {
    return text;
  }
  return `${text.slice(0, 41)}...`;
}

export function applyIndentAtIndex(doc: JSONContent, blockIndex: number): JSONContent | null {
  const content = asTopLevelBlocks(doc);
  const current = content[blockIndex];
  const previous = content[blockIndex - 1];
  if (!isNestable(current) || !isNestable(previous) || blockIndex <= 0) {
    return null;
  }

  const next = cloneDoc(doc);
  const nextContent = asTopLevelBlocks(next);
  const nextCurrent = nextContent[blockIndex];
  const nextPrevious = nextContent[blockIndex - 1];
  if (!nextCurrent || !nextPrevious) {
    return null;
  }

  const parentUid = ensureUid(nextPrevious);
  ensureUid(nextCurrent);
  const parentIndent = Number(asAttrs(nextPrevious).indentLevel ?? 0);

  if (!nextCurrent.attrs || typeof nextCurrent.attrs !== "object") {
    nextCurrent.attrs = {};
  }
  const attrs = nextCurrent.attrs as BlockAttrs;
  attrs.parentBlockUid = parentUid;
  attrs.indentLevel = parentIndent + 1;

  return next;
}

export function applyOutdentAtIndex(doc: JSONContent, blockIndex: number): JSONContent | null {
  const content = asTopLevelBlocks(doc);
  const current = content[blockIndex];
  if (!isNestable(current)) {
    return null;
  }

  const currentAttrs = asAttrs(current);
  const parentUid = currentAttrs.parentBlockUid;
  if (!parentUid) {
    return null;
  }

  const parentNode = findBlockByUid(content, parentUid);
  const grandParentUid = asAttrs(parentNode ?? undefined).parentBlockUid ?? null;
  const grandParentNode = findBlockByUid(content, grandParentUid);
  const grandParentIndent = Number(asAttrs(grandParentNode ?? undefined).indentLevel ?? -1);

  const next = cloneDoc(doc);
  const nextContent = asTopLevelBlocks(next);
  const nextCurrent = nextContent[blockIndex];
  if (!nextCurrent) {
    return null;
  }
  if (!nextCurrent.attrs || typeof nextCurrent.attrs !== "object") {
    nextCurrent.attrs = {};
  }
  const attrs = nextCurrent.attrs as BlockAttrs;
  attrs.parentBlockUid = grandParentUid;
  attrs.indentLevel = Math.max(0, grandParentIndent + 1);
  return next;
}

export function formatHierarchyHint(args: {
  canIndent: boolean;
  canOutdent: boolean;
  parentPreviewText: string | null;
}): string {
  if (args.canIndent && args.parentPreviewText) {
    return `Tab nest under: ${args.parentPreviewText}`;
  }
  if (args.canIndent) {
    return "Tab to nest under previous block";
  }
  if (args.canOutdent) {
    return "Shift+Tab to outdent";
  }
  return "No nesting action available for current block";
}
