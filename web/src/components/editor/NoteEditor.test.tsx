import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NoteEditor } from "./NoteEditor";
import {
  getNote,
  queueNoteProcessing,
  saveNote,
} from "../../lib/api-client";

vi.mock("../../lib/api-client", () => ({
  getNote: vi.fn(),
  saveNote: vi.fn(),
  queueNoteProcessing: vi.fn(),
  fetchProcessingStatus: vi.fn(),
}));

vi.mock("./TipTapEditor", () => ({
  TipTapEditor: ({
    value,
    onUpdate,
    onBlur,
    disabled,
  }: {
    value: Record<string, unknown>;
    onUpdate: (payload: { json: Record<string, unknown>; text: string }) => void;
    onBlur: () => void;
    disabled?: boolean;
  }) => {
    const firstBlock = Array.isArray(value.content) ? value.content[0] : undefined;
    const firstText =
      firstBlock &&
      typeof firstBlock === "object" &&
      Array.isArray((firstBlock as { content?: unknown[] }).content)
        ? (firstBlock as { content: unknown[] }).content[0]
        : undefined;
    const plainText =
      firstText && typeof firstText === "object" && typeof (firstText as { text?: unknown }).text === "string"
        ? (firstText as { text: string }).text
        : "";

    return (
      <textarea
        aria-label="TipTap editor"
        data-testid="tiptap-editor"
        value={plainText}
        disabled={disabled}
        onChange={(event) =>
          onUpdate({
            json: {
              type: "doc",
              content: [
                {
                  type: "paragraph",
                  content: [{ type: "text", text: event.target.value }],
                },
              ],
            },
            text: event.target.value,
          })
        }
        onBlur={onBlur}
      />
    );
  },
}));

describe("NoteEditor", () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("loads existing note content into the editor", async () => {
    vi.mocked(getNote).mockResolvedValue({
      note_id: "note-1",
      content_json: {
        type: "doc",
        content: [
          { type: "paragraph", content: [{ type: "text", text: "Loaded text" }] },
        ],
      },
      content_text: "Loaded text",
      updated_at: "2026-03-01T13:00:00Z",
      version: 1,
    });
    vi.mocked(saveNote).mockResolvedValue({
      note_id: "note-1",
      saved_at: "2026-03-01T13:00:01Z",
      version: 1,
    });
    vi.mocked(queueNoteProcessing).mockResolvedValue({
      job_id: "job-1",
      status: "queued",
    });

    render(<NoteEditor noteId="note-1" baseUrl="http://localhost:8000" />);

    await waitFor(() => {
      expect(screen.getByLabelText("TipTap editor")).toHaveValue("Loaded text");
    });
  });

  it("marks note dirty on edit and autosaves after debounce", async () => {
    vi.mocked(getNote).mockResolvedValue({
      note_id: "note-2",
      content_json: { type: "doc", content: [] },
      content_text: "",
      updated_at: "2026-03-01T13:01:00Z",
      version: 1,
    });
    vi.mocked(saveNote).mockResolvedValue({
      note_id: "note-2",
      saved_at: "2026-03-01T13:01:01Z",
      version: 2,
    });
    vi.mocked(queueNoteProcessing).mockResolvedValue({
      job_id: "job-2",
      status: "queued",
    });

    render(
      <NoteEditor
        noteId="note-2"
        baseUrl="http://localhost:8000"
        autosaveDebounceMs={10}
        processDebounceMs={30}
      />,
    );

    await waitFor(() =>
      expect(screen.getByLabelText("TipTap editor")).not.toBeDisabled(),
    );
    const input = screen.getByLabelText("TipTap editor");
    fireEvent.change(input, { target: { value: "Updated content" } });

    expect(screen.getByTestId("dirty-flag")).toHaveTextContent("dirty");

    await waitFor(() => expect(saveNote).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.getByTestId("save-status")).toHaveTextContent("saved"),
    );
    await waitFor(() => expect(queueNoteProcessing).toHaveBeenCalledTimes(1));
  });

  it("surfaces save errors", async () => {
    vi.mocked(getNote).mockResolvedValue({
      note_id: "note-3",
      content_json: { type: "doc", content: [] },
      content_text: "",
      updated_at: "2026-03-01T13:02:00Z",
      version: 1,
    });
    vi.mocked(saveNote).mockRejectedValue(new Error("save failed"));
    vi.mocked(queueNoteProcessing).mockResolvedValue({
      job_id: "job-3",
      status: "queued",
    });

    render(
      <NoteEditor
        noteId="note-3"
        baseUrl="http://localhost:8000"
        autosaveDebounceMs={10}
        processDebounceMs={30}
      />,
    );

    await waitFor(() =>
      expect(screen.getByLabelText("TipTap editor")).not.toBeDisabled(),
    );
    const input = screen.getByLabelText("TipTap editor");
    fireEvent.change(input, { target: { value: "Trigger error" } });

    await waitFor(() =>
      expect(screen.getByTestId("save-status")).toHaveTextContent("error"),
    );
  });
});
