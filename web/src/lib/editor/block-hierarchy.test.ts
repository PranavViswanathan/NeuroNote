import { describe, expect, it } from "vitest";
import type { JSONContent } from "@tiptap/react";

import {
  applyIndentAtIndex,
  applyOutdentAtIndex,
  computeHierarchyActions,
  formatHierarchyHint,
  resolveParentPreviewText,
} from "./block-hierarchy";

describe("block hierarchy", () => {
  it("indents a block under the previous block", () => {
    const doc: JSONContent = {
      type: "doc",
      content: [
        { type: "heading", attrs: { level: 1, blockUid: "h1-root", indentLevel: 0 }, content: [] },
        { type: "paragraph", attrs: { blockUid: "p-child", indentLevel: 0 }, content: [] },
      ],
    };

    const next = applyIndentAtIndex(doc, 1);
    expect(next).not.toBeNull();
    expect(next?.content?.[1]).toMatchObject({
      attrs: {
        parentBlockUid: "h1-root",
        indentLevel: 1,
      },
    });
  });

  it("outdents a nested block to its grandparent", () => {
    const doc: JSONContent = {
      type: "doc",
      content: [
        { type: "heading", attrs: { level: 1, blockUid: "h1-root", indentLevel: 0 }, content: [] },
        {
          type: "heading",
          attrs: { level: 2, blockUid: "h2-child", parentBlockUid: "h1-root", indentLevel: 1 },
          content: [],
        },
        {
          type: "paragraph",
          attrs: { blockUid: "p-grandchild", parentBlockUid: "h2-child", indentLevel: 2 },
          content: [],
        },
      ],
    };

    const next = applyOutdentAtIndex(doc, 2);
    expect(next).not.toBeNull();
    expect(next?.content?.[2]).toMatchObject({
      attrs: {
        parentBlockUid: "h1-root",
        indentLevel: 1,
      },
    });
  });

  it("reports valid indentation actions for heading/paragraph", () => {
    const doc: JSONContent = {
      type: "doc",
      content: [
        { type: "heading", attrs: { blockUid: "head", indentLevel: 0 }, content: [] },
        { type: "paragraph", attrs: { blockUid: "para", indentLevel: 0 }, content: [] },
      ],
    };

    const state = computeHierarchyActions(doc, 1);
    expect(state.canIndent).toBe(true);
    expect(state.canOutdent).toBe(false);
    expect(state.parentCandidateUid).toBe("head");
  });

  it("resolves readable parent preview text from previous block", () => {
    const doc: JSONContent = {
      type: "doc",
      content: [
        {
          type: "heading",
          attrs: { blockUid: "head", indentLevel: 0 },
          content: [{ type: "text", text: "This is parent heading text" }],
        },
        { type: "paragraph", attrs: { blockUid: "para", indentLevel: 0 }, content: [] },
      ],
    };
    expect(resolveParentPreviewText(doc, 1)).toContain("This is parent heading text");
  });

  it("formats hierarchy hint with parent preview", () => {
    const hint = formatHierarchyHint({
      canIndent: true,
      canOutdent: false,
      parentPreviewText: "Parent heading",
    });
    expect(hint).toContain("Parent heading");
    expect(hint).toContain("Tab");
  });
});
