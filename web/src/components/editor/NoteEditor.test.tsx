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
      expect(screen.getByLabelText("Note editor")).toHaveValue("Loaded text");
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
      expect(screen.getByLabelText("Note editor")).not.toBeDisabled(),
    );
    const input = screen.getByLabelText("Note editor");
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
      expect(screen.getByLabelText("Note editor")).not.toBeDisabled(),
    );
    const input = screen.getByLabelText("Note editor");
    fireEvent.change(input, { target: { value: "Trigger error" } });

    await waitFor(() =>
      expect(screen.getByTestId("save-status")).toHaveTextContent("error"),
    );
  });
});
