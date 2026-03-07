import { describe, expect, it } from "vitest";

import { extractPlainText } from "./text-extract";

describe("extractPlainText", () => {
  it("extracts text from headings and paragraphs with line breaks", () => {
    const doc = {
      type: "doc",
      content: [
        {
          type: "heading",
          content: [{ type: "text", text: "Graph Thinking" }],
        },
        {
          type: "paragraph",
          content: [{ type: "text", text: "Knowledge maps improve recall." }],
        },
      ],
    };

    expect(extractPlainText(doc)).toBe("Graph Thinking\nKnowledge maps improve recall.");
  });

  it("extracts nested list text", () => {
    const doc = {
      type: "doc",
      content: [
        {
          type: "bulletList",
          content: [
            {
              type: "listItem",
              content: [
                {
                  type: "paragraph",
                  content: [{ type: "text", text: "First item" }],
                },
              ],
            },
            {
              type: "listItem",
              content: [
                {
                  type: "paragraph",
                  content: [{ type: "text", text: "Second item" }],
                },
              ],
            },
          ],
        },
      ],
    };

    expect(extractPlainText(doc)).toBe("First item\nSecond item");
  });

  it("returns empty string for empty documents", () => {
    expect(extractPlainText({ type: "doc", content: [] })).toBe("");
  });
});
