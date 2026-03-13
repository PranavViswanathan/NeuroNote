import React from "react";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NotesWorkspace } from "./NotesWorkspace";
import { deleteNote, getNote, listNotes, saveNote } from "../../lib/api-client";

vi.mock("../../lib/api-client", () => ({
  listNotes: vi.fn(),
  saveNote: vi.fn(),
  deleteNote: vi.fn(),
  getNote: vi.fn(),
}));

vi.mock("../editor/NoteEditor", () => ({
  NoteEditor: ({ noteId }: { noteId: string }) => <div data-testid="active-note-id">{noteId}</div>,
}));

function noteSummary(
  noteId: string,
  overrides?: Record<string, unknown>,
): {
  note_id: string;
  note_title: string;
  subject_id: string;
  tags: string[];
  is_pinned: boolean;
  is_archived: boolean;
  content_text: string;
  updated_at: string;
  version: number;
} {
  return {
    note_id: noteId,
    note_title: `Title ${noteId}`,
    subject_id: "inbox",
    tags: [],
    is_pinned: false,
    is_archived: false,
    content_text: `Text ${noteId}`,
    updated_at: "2026-03-12T20:00:00Z",
    version: 1,
    ...overrides,
  };
}

describe("NotesWorkspace", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.localStorage.clear();
  });

  it("loads note list and opens the first note", async () => {
    vi.mocked(listNotes).mockResolvedValue({
      items: [noteSummary("note-a"), noteSummary("note-b")],
      total: 2,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    await waitFor(() => {
      expect(screen.getByTestId("active-note-id")).toHaveTextContent("note-a");
    });
  });

  it("creates a note and selects it", async () => {
    vi.mocked(listNotes)
      .mockResolvedValueOnce({
        items: [noteSummary("note-a")],
        total: 1,
      })
      .mockResolvedValueOnce({
        items: [noteSummary("note-a"), noteSummary("note-new")],
        total: 2,
      });
    vi.mocked(saveNote).mockResolvedValue({
      note_id: "note-new",
      saved_at: "2026-03-12T20:01:00Z",
      version: 1,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    await screen.findByRole("listbox", { name: "Notes" });
    fireEvent.click(screen.getByRole("button", { name: "New note" }));

    await waitFor(() => {
      expect(saveNote).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByTestId("active-note-id")).toHaveTextContent("note-new");
    });
  });

  it("guards against duplicate note creation on rapid repeated clicks", async () => {
    let resolveSave!: (value: { note_id: string; saved_at: string; version: number }) => void;
    const pendingSave = new Promise<{ note_id: string; saved_at: string; version: number }>(
      (resolve) => {
        resolveSave = resolve;
      },
    );

    vi.mocked(listNotes)
      .mockResolvedValueOnce({
        items: [noteSummary("note-a")],
        total: 1,
      })
      .mockResolvedValueOnce({
        items: [noteSummary("note-a"), noteSummary("note-new")],
        total: 2,
      });
    vi.mocked(saveNote).mockReturnValue(pendingSave);

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    const createButton = await screen.findByRole("button", { name: "New note" });
    fireEvent.click(createButton);
    fireEvent.click(createButton);

    expect(saveNote).toHaveBeenCalledTimes(1);
    expect(createButton).toBeDisabled();

    resolveSave({
      note_id: "note-new",
      saved_at: "2026-03-12T20:01:00Z",
      version: 1,
    });

    await waitFor(() => {
      expect(screen.getByTestId("active-note-id")).toHaveTextContent("note-new");
    });
  });

  it("renders pinned notes separately from all notes", async () => {
    vi.mocked(listNotes).mockResolvedValue({
      items: [
        noteSummary("note-a", { note_title: "Pinned A", is_pinned: true }),
        noteSummary("note-b", { note_title: "Regular B", is_pinned: false }),
      ],
      total: 2,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    const pinnedSection = await screen.findByTestId("notes-section-pinned");
    expect(within(pinnedSection).getByRole("button", { name: /Pinned A/ })).toBeInTheDocument();

    const allSection = screen.getByTestId("notes-section-all");
    expect(within(allSection).getByRole("button", { name: /Regular B/ })).toBeInTheDocument();
    expect(within(allSection).queryByRole("button", { name: /Pinned A/ })).not.toBeInTheDocument();
  });

  it("opens note context menu on right click and removes top-level rename/delete actions", async () => {
    vi.mocked(listNotes).mockResolvedValue({
      items: [noteSummary("note-a", { note_title: "Context A" })],
      total: 1,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    expect(screen.queryByRole("button", { name: "Rename note" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete note" })).not.toBeInTheDocument();

    const allSection = screen.getByTestId("notes-section-all");
    await waitFor(() => {
      expect(within(allSection).getByRole("button", { name: /Context A/ })).toBeInTheDocument();
    });
    const noteButton = within(allSection).getByRole("button", { name: /Context A/ });
    fireEvent.contextMenu(noteButton);

    expect(await screen.findByRole("menuitem", { name: "Rename note" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Delete note" })).toBeInTheDocument();
  });

  it("renames a note from context menu action", async () => {
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("Renamed from menu");
    vi.mocked(listNotes)
      .mockResolvedValueOnce({
        items: [noteSummary("note-a", { note_title: "Context A" })],
        total: 1,
      })
      .mockResolvedValueOnce({
        items: [noteSummary("note-a", { note_title: "Renamed from menu" })],
        total: 1,
      });
    vi.mocked(getNote).mockResolvedValue({
      note_id: "note-a",
      note_title: "Context A",
      subject_id: "inbox",
      tags: [],
      is_pinned: false,
      is_archived: false,
      content_json: { type: "doc", content: [] },
      content_text: "Text note-a",
      updated_at: "2026-03-12T20:00:00Z",
      version: 1,
    });
    vi.mocked(saveNote).mockResolvedValue({
      note_id: "note-a",
      saved_at: "2026-03-12T20:01:00Z",
      version: 2,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    const allSection = screen.getByTestId("notes-section-all");
    await waitFor(() => {
      expect(within(allSection).getByRole("button", { name: /Context A/ })).toBeInTheDocument();
    });
    const noteButton = within(allSection).getByRole("button", { name: /Context A/ });
    fireEvent.contextMenu(noteButton);
    fireEvent.click(await screen.findByRole("menuitem", { name: "Rename note" }));

    await waitFor(() => {
      expect(saveNote).toHaveBeenCalled();
    });
    expect(vi.mocked(saveNote).mock.calls.at(-1)?.[1]).toMatchObject({
      note_id: "note-a",
      note_title: "Renamed from menu",
    });
    expect(promptSpy).toHaveBeenCalled();
    promptSpy.mockRestore();
  });

  it("deletes selected note from context menu action", async () => {
    vi.mocked(listNotes)
      .mockResolvedValueOnce({
        items: [noteSummary("note-a"), noteSummary("note-b")],
        total: 2,
      })
      .mockResolvedValueOnce({
        items: [noteSummary("note-b")],
        total: 1,
      });
    vi.mocked(deleteNote).mockResolvedValue();

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    const allSection = screen.getByTestId("notes-section-all");
    await waitFor(() => {
      expect(within(allSection).getByRole("button", { name: /Title note-a/ })).toBeInTheDocument();
    });
    const noteButton = within(allSection).getByRole("button", { name: /Title note-a/ });
    fireEvent.contextMenu(noteButton);
    fireEvent.click(await screen.findByRole("menuitem", { name: "Delete note" }));

    await waitFor(() => {
      expect(deleteNote).toHaveBeenCalledWith("http://localhost:8000", "note-a");
    });
    await waitFor(() => {
      expect(screen.getByTestId("active-note-id")).toHaveTextContent("note-b");
    });
  });

  it("refreshes list automatically after search input debounce", async () => {
    vi.mocked(listNotes)
      .mockResolvedValueOnce({
        items: [noteSummary("note-a", { note_title: "Alpha" })],
        total: 1,
      })
      .mockResolvedValueOnce({
        items: [noteSummary("note-b", { note_title: "Beta" })],
        total: 1,
      });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    await waitFor(() => {
      expect(listNotes).toHaveBeenCalledTimes(1);
    });

    fireEvent.change(screen.getByLabelText("Search"), { target: { value: "beta" } });
    await waitFor(() => {
      expect(listNotes).toHaveBeenCalledTimes(2);
    });
    expect(vi.mocked(listNotes).mock.calls.at(-1)?.[1]).toMatchObject({
      search: "beta",
    });
  });

  it("renders note content preview snippet in list rows", async () => {
    vi.mocked(listNotes).mockResolvedValue({
      items: [
        noteSummary("note-a", {
          note_title: "Preview Note",
          content_text: "A long preview sentence from this note body",
        }),
      ],
      total: 1,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    await waitFor(() => {
      expect(screen.getByText(/A long preview sentence/)).toBeInTheDocument();
    });
  });

  it("opens context menu via keyboard shortcut", async () => {
    vi.mocked(listNotes).mockResolvedValue({
      items: [noteSummary("note-a", { note_title: "Keyboard Menu" })],
      total: 1,
    });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    const allSection = screen.getByTestId("notes-section-all");
    await waitFor(() => {
      expect(within(allSection).getByRole("button", { name: /Keyboard Menu/ })).toBeInTheDocument();
    });
    const noteButton = within(allSection).getByRole("button", { name: /Keyboard Menu/ });
    noteButton.focus();
    fireEvent.keyDown(noteButton, { key: "F10", shiftKey: true });

    expect(await screen.findByRole("menuitem", { name: "Rename note" })).toBeInTheDocument();
  });

  it("shows loading state while list request is pending", async () => {
    vi.mocked(listNotes).mockImplementation(
      () => new Promise(() => {}),
    );

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);
    expect(await screen.findByText("Loading notes...")).toBeInTheDocument();
  });

  it("shows retry action after load failure and retries successfully", async () => {
    vi.mocked(listNotes)
      .mockRejectedValueOnce(new Error("boom"))
      .mockResolvedValueOnce({
        items: [noteSummary("note-a", { note_title: "Recovered Note" })],
        total: 1,
      });

    render(<NotesWorkspace baseUrl="http://localhost:8000" />);

    expect(await screen.findByText("Failed to load notes")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(listNotes).toHaveBeenCalledTimes(2);
    });
    await waitFor(() => {
      const allSection = screen.getByTestId("notes-section-all");
      expect(within(allSection).getByRole("button", { name: /Recovered Note/ })).toBeInTheDocument();
    });
  });
});
