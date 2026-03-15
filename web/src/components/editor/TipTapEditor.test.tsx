import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TipTapEditor } from "./TipTapEditor";

describe("TipTapEditor", () => {
  it("renders loaded content immediately with multiline block structure", async () => {
    const onUpdate = vi.fn();
    const onBlur = vi.fn();

    render(
      <TipTapEditor
        value={{
          type: "doc",
          content: [
            { type: "paragraph", content: [{ type: "text", text: "First line" }] },
            { type: "paragraph", content: [{ type: "text", text: "Second line" }] },
          ],
        }}
        onUpdate={onUpdate}
        onBlur={onBlur}
      />,
    );

    const editor = await screen.findByTestId("tiptap-editor");
    await waitFor(() => {
      expect(editor.textContent).toContain("First line");
      expect(editor.textContent).toContain("Second line");
    });
    expect(editor.className).toContain("tiptap-editor");
    expect(editor.querySelector(".ProseMirror")).not.toBeNull();
  });

  it("renders the core block command buttons", async () => {
    render(
      <TipTapEditor
        value={{ type: "doc", content: [{ type: "paragraph", content: [] }] }}
        onUpdate={vi.fn()}
        onBlur={vi.fn()}
      />,
    );

    await screen.findByRole("button", { name: "Paragraph" });
    expect(screen.getByRole("button", { name: "H1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "H2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "H3" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Checklist" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Math Inline" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Math Block" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Image" })).toBeInTheDocument();
    expect(screen.getByText("No nesting action available for current block")).toBeInTheDocument();
  });

  it("opens command palette from keyboard fallback", async () => {
    render(
      <TipTapEditor
        value={{
          type: "doc",
          content: [{ type: "paragraph", content: [{ type: "text", text: "hello" }] }],
        }}
        onUpdate={vi.fn()}
        onBlur={vi.fn()}
      />,
    );

    const editor = await screen.findByTestId("tiptap-editor");
    const proseMirror = editor.querySelector(".ProseMirror");
    expect(proseMirror).not.toBeNull();
    if (!proseMirror) {
      throw new Error("Missing ProseMirror editor");
    }

    fireEvent.keyDown(proseMirror, { key: "k", ctrlKey: true });

    await screen.findByRole("listbox", { name: "Editor commands" });
  });
});
