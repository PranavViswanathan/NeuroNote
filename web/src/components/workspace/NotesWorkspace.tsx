"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent, MouseEvent as ReactMouseEvent } from "react";

import { NoteEditor } from "../editor/NoteEditor";
import { deleteNote, getNote, listNotes, saveNote } from "../../lib/api-client";
import type { WorkspaceFilters } from "../../lib/workspace/types";
import type { NoteSummary } from "../../../../shared/contracts/ts/v1/note";

const SELECTED_NOTE_STORAGE_KEY = "neuronote.workspace.selected";
const RECENT_NOTES_STORAGE_KEY = "neuronote.workspace.recent";
const MAX_RECENT_NOTES = 5;
const FILTER_DEBOUNCE_MS = 250;

interface NotesWorkspaceProps {
  baseUrl: string;
  initialNoteId?: string;
}

interface WorkspaceMetadataSavedPayload {
  noteId: string;
  noteTitle: string;
  subjectId: string;
  tags: string[];
  isPinned: boolean;
  isArchived: boolean;
  updatedAt: string;
  version: number;
}

interface NoteContextMenuState {
  noteId: string;
  x: number;
  y: number;
}

function compareByWorkspaceOrder(left: NoteSummary, right: NoteSummary): number {
  if (left.is_pinned !== right.is_pinned) {
    return left.is_pinned ? -1 : 1;
  }
  const updatedDiff = right.updated_at.localeCompare(left.updated_at);
  if (updatedDiff !== 0) {
    return updatedDiff;
  }
  return left.note_id.localeCompare(right.note_id);
}

function sortWorkspaceNotes(items: NoteSummary[]): NoteSummary[] {
  return [...items].sort(compareByWorkspaceOrder);
}

function pickFallbackSelection(items: NoteSummary[]): string | null {
  return sortWorkspaceNotes(items)[0]?.note_id ?? null;
}

function makeNewNoteId(): string {
  return `note-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

function loadRecentNotes(): string[] {
  const raw = window.localStorage.getItem(RECENT_NOTES_STORAGE_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((item): item is string => typeof item === "string");
  } catch {
    return [];
  }
}

function persistRecentNotes(noteIds: string[]): void {
  window.localStorage.setItem(
    RECENT_NOTES_STORAGE_KEY,
    JSON.stringify(noteIds.slice(0, MAX_RECENT_NOTES)),
  );
}

function toPreview(content: string): string {
  const normalized = content.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "No content yet";
  }
  if (normalized.length <= 96) {
    return normalized;
  }
  return `${normalized.slice(0, 93)}...`;
}

function toDisplayDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown";
  }
  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function NotesWorkspace({ baseUrl, initialNoteId }: NotesWorkspaceProps) {
  const [notes, setNotes] = useState<NoteSummary[]>([]);
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(initialNoteId ?? null);
  const [highlightedNoteId, setHighlightedNoteId] = useState<string | null>(initialNoteId ?? null);
  const [recentNoteIds, setRecentNoteIds] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingNote, setIsCreatingNote] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<NoteContextMenuState | null>(null);
  const createInFlightRef = useRef(false);
  const contextMenuRef = useRef<HTMLUListElement | null>(null);
  const filtersInitializedRef = useRef(false);

  const filters: WorkspaceFilters = useMemo(
    () => ({
      search,
      subjectId: subjectFilter,
      tag: tagFilter,
      showArchived,
    }),
    [search, showArchived, subjectFilter, tagFilter],
  );

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  const openContextMenu = useCallback(
    (noteId: string, x: number, y: number) => {
      setSelectedNoteId(noteId);
      setContextMenu({
        noteId,
        x: x + 8,
        y: y + 8,
      });
    },
    [],
  );

  const refreshNotes = useCallback(
    async (preferredNoteId?: string | null) => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const response = await listNotes(baseUrl, {
          limit: 100,
          offset: 0,
          search: filters.search.trim() || undefined,
          subject_id: filters.subjectId.trim() || undefined,
          tag: filters.tag.trim() || undefined,
          is_archived: filters.showArchived,
        });
        setNotes(sortWorkspaceNotes(response.items));

        setSelectedNoteId((current) => {
          const persisted = window.localStorage.getItem(SELECTED_NOTE_STORAGE_KEY);
          const candidateIds = [preferredNoteId, current, initialNoteId, persisted];
          for (const candidate of candidateIds) {
            if (!candidate) {
              continue;
            }
            if (response.items.some((note) => note.note_id === candidate)) {
              return candidate;
            }
          }
          return pickFallbackSelection(response.items);
        });
      } catch {
        setErrorMessage("Failed to load notes");
        setNotes([]);
        setSelectedNoteId(null);
      } finally {
        setIsLoading(false);
      }
    },
    [baseUrl, filters, initialNoteId],
  );

  useEffect(() => {
    setRecentNoteIds(loadRecentNotes());
    void refreshNotes(initialNoteId ?? null);
  }, [initialNoteId, refreshNotes]);

  useEffect(() => {
    if (!filtersInitializedRef.current) {
      filtersInitializedRef.current = true;
      return;
    }
    const timer = window.setTimeout(() => {
      void refreshNotes(null);
    }, FILTER_DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
    };
  }, [refreshNotes, search, showArchived, subjectFilter, tagFilter]);

  useEffect(() => {
    if (!selectedNoteId) {
      return;
    }
    window.localStorage.setItem(SELECTED_NOTE_STORAGE_KEY, selectedNoteId);
    setRecentNoteIds((current) => {
      const next = [selectedNoteId, ...current.filter((item) => item !== selectedNoteId)];
      persistRecentNotes(next);
      return next.slice(0, MAX_RECENT_NOTES);
    });
  }, [selectedNoteId]);

  useEffect(() => {
    if (selectedNoteId && notes.some((note) => note.note_id === selectedNoteId)) {
      setHighlightedNoteId(selectedNoteId);
      return;
    }
    const firstUnpinned = notes.find((note) => !note.is_pinned);
    const fallback = firstUnpinned ?? notes[0] ?? null;
    setHighlightedNoteId(fallback?.note_id ?? null);
  }, [notes, selectedNoteId]);

  useEffect(() => {
    if (!contextMenu) {
      return;
    }

    const handleMouseDown = (event: MouseEvent) => {
      if (!contextMenuRef.current) {
        return;
      }
      const target = event.target;
      if (!(target instanceof Node)) {
        return;
      }
      if (!contextMenuRef.current.contains(target)) {
        closeContextMenu();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeContextMenu();
      }
    };

    window.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [closeContextMenu, contextMenu]);

  const recentNotes = useMemo(() => {
    const index = new Map(notes.map((note) => [note.note_id, note]));
    return recentNoteIds.map((noteId) => index.get(noteId)).filter((item): item is NoteSummary => Boolean(item));
  }, [notes, recentNoteIds]);
  const pinnedNotes = useMemo(() => notes.filter((note) => note.is_pinned), [notes]);
  const unpinnedNotes = useMemo(() => notes.filter((note) => !note.is_pinned), [notes]);
  const contextNote = useMemo(
    () => (contextMenu ? notes.find((item) => item.note_id === contextMenu.noteId) ?? null : null),
    [contextMenu, notes],
  );

  const handleMetadataSaved = useCallback(
    async (payload: WorkspaceMetadataSavedPayload) => {
      setNotes((current) =>
        sortWorkspaceNotes(
          current.map((item) =>
            item.note_id === payload.noteId
              ? {
                  ...item,
                  note_title: payload.noteTitle,
                  subject_id: payload.subjectId,
                  tags: payload.tags,
                  is_pinned: payload.isPinned,
                  is_archived: payload.isArchived,
                  updated_at: payload.updatedAt,
                  version: payload.version,
                }
              : item,
          ),
        ),
      );
      await refreshNotes(payload.noteId);
    },
    [refreshNotes],
  );

  const handleCreateNote = useCallback(async () => {
    if (createInFlightRef.current) {
      return;
    }
    createInFlightRef.current = true;
    setIsCreatingNote(true);
    const newNoteId = makeNewNoteId();
    try {
      const created = await saveNote(baseUrl, {
        note_id: newNoteId,
        note_title: "Untitled",
        subject_id: "inbox",
        tags: [],
        is_pinned: false,
        is_archived: false,
        content_json: { type: "doc", content: [] },
        content_text: " ",
        updated_at: new Date().toISOString(),
      });
      await refreshNotes(created.note_id);
    } catch {
      setErrorMessage("Failed to create note");
    } finally {
      createInFlightRef.current = false;
      setIsCreatingNote(false);
    }
  }, [baseUrl, refreshNotes]);

  const handleRenameNote = useCallback(
    async (noteId: string) => {
      const selected = notes.find((item) => item.note_id === noteId);
      if (!selected) {
        return;
      }

      const nextTitle = window.prompt("Rename note", selected.note_title);
      if (nextTitle == null) {
        closeContextMenu();
        return;
      }
      const trimmedTitle = nextTitle.trim();
      if (!trimmedTitle || trimmedTitle === selected.note_title) {
        closeContextMenu();
        return;
      }

      const previousNotes = notes;
      setNotes((current) =>
        sortWorkspaceNotes(
          current.map((item) =>
            item.note_id === noteId
              ? {
                  ...item,
                  note_title: trimmedTitle,
                  updated_at: new Date().toISOString(),
                }
              : item,
          ),
        ),
      );
      closeContextMenu();

      try {
        const existing = await getNote(baseUrl, noteId);
        await saveNote(baseUrl, {
          note_id: existing.note_id,
          note_title: trimmedTitle,
          subject_id: existing.subject_id,
          tags: existing.tags,
          is_pinned: existing.is_pinned,
          is_archived: existing.is_archived,
          content_json: existing.content_json,
          content_text: existing.content_text,
          updated_at: new Date().toISOString(),
        });
        await refreshNotes(noteId);
      } catch {
        setNotes(previousNotes);
        setErrorMessage("Failed to rename note");
      }
    },
    [baseUrl, closeContextMenu, notes, refreshNotes],
  );

  const handleDeleteNote = useCallback(
    async (noteId: string) => {
      const previousNotes = notes;
      const previousSelected = selectedNoteId;
      const remaining = notes.filter((item) => item.note_id !== noteId);

      setNotes(sortWorkspaceNotes(remaining));
      setSelectedNoteId((current) => {
        if (current !== noteId) {
          return current;
        }
        return pickFallbackSelection(remaining);
      });
      setHighlightedNoteId((current) => {
        if (current !== noteId) {
          return current;
        }
        return pickFallbackSelection(remaining);
      });
      closeContextMenu();

      try {
        await deleteNote(baseUrl, noteId);
        await refreshNotes(null);
      } catch {
        setNotes(previousNotes);
        setSelectedNoteId(previousSelected);
        setHighlightedNoteId(previousSelected ?? pickFallbackSelection(previousNotes));
        setErrorMessage("Failed to delete note");
      }
    },
    [baseUrl, closeContextMenu, notes, refreshNotes, selectedNoteId],
  );

  const handleTogglePinnedNote = useCallback(
    async (noteId: string) => {
      const target = notes.find((item) => item.note_id === noteId);
      if (!target) {
        closeContextMenu();
        return;
      }
      const previousNotes = notes;

      setNotes((current) =>
        sortWorkspaceNotes(
          current.map((item) =>
            item.note_id === noteId
              ? {
                  ...item,
                  is_pinned: !item.is_pinned,
                  updated_at: new Date().toISOString(),
                }
              : item,
          ),
        ),
      );
      closeContextMenu();

      try {
        const existing = await getNote(baseUrl, noteId);
        await saveNote(baseUrl, {
          note_id: existing.note_id,
          note_title: existing.note_title,
          subject_id: existing.subject_id,
          tags: existing.tags,
          is_pinned: !existing.is_pinned,
          is_archived: existing.is_archived,
          content_json: existing.content_json,
          content_text: existing.content_text,
          updated_at: new Date().toISOString(),
        });
        await refreshNotes(noteId);
      } catch {
        setNotes(previousNotes);
        setErrorMessage("Failed to update pin status");
      }
    },
    [baseUrl, closeContextMenu, notes, refreshNotes],
  );

  const handleListKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLUListElement>) => {
      if (!unpinnedNotes.length) {
        return;
      }
      const activeIndex = unpinnedNotes.findIndex((note) => note.note_id === highlightedNoteId);
      const safeIndex = activeIndex >= 0 ? activeIndex : 0;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        const nextIndex = Math.min(safeIndex + 1, unpinnedNotes.length - 1);
        setHighlightedNoteId(unpinnedNotes[nextIndex]?.note_id ?? null);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        const nextIndex = Math.max(safeIndex - 1, 0);
        setHighlightedNoteId(unpinnedNotes[nextIndex]?.note_id ?? null);
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const target = unpinnedNotes[safeIndex];
        if (target) {
          setSelectedNoteId(target.note_id);
        }
      }
    },
    [highlightedNoteId, unpinnedNotes],
  );

  const handleNoteContextMenu = useCallback(
    (event: ReactMouseEvent<HTMLButtonElement>, noteId: string) => {
      event.preventDefault();
      openContextMenu(noteId, event.clientX, event.clientY);
    },
    [openContextMenu],
  );

  const handleNoteContextMenuKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLButtonElement>, noteId: string) => {
      if ((event.shiftKey && event.key === "F10") || event.key === "ContextMenu") {
        event.preventDefault();
        const rect = event.currentTarget.getBoundingClientRect();
        openContextMenu(noteId, rect.left + 8, rect.bottom + 8);
      }
    },
    [openContextMenu],
  );

  const renderNoteButton = useCallback(
    (note: NoteSummary, highlighted = false) => (
      <button
        type="button"
        className={`note-list-button${note.note_id === selectedNoteId ? " selected" : ""}${highlighted ? " highlighted" : ""}`}
        onClick={() => {
          setSelectedNoteId(note.note_id);
          setHighlightedNoteId(note.note_id);
          closeContextMenu();
        }}
        onContextMenu={(event) => handleNoteContextMenu(event, note.note_id)}
        onKeyDown={(event) => handleNoteContextMenuKeyDown(event, note.note_id)}
        aria-haspopup="menu"
      >
        <span className="note-list-title">{note.note_title}</span>
        <span className="note-list-preview">{toPreview(note.content_text)}</span>
        <span className="note-list-meta-row">
          <span className="note-list-meta">{note.subject_id}</span>
          <span className="note-list-date">{toDisplayDate(note.updated_at)}</span>
        </span>
      </button>
    ),
    [closeContextMenu, handleNoteContextMenu, handleNoteContextMenuKeyDown, selectedNoteId],
  );

  return (
    <section className="notes-workspace" data-testid="notes-workspace">
      <aside className="notes-sidebar">
        <header className="notes-sidebar-header">
          <div>
            <h1>NeuroNote</h1>
            <p>Focused notes with graph-aware processing</p>
          </div>
          <button type="button" className="primary-action-button" onClick={() => void handleCreateNote()} disabled={isCreatingNote}>
            New note
          </button>
        </header>

        <div className="workspace-stat-grid" aria-label="Workspace summary">
          <article className="workspace-stat-card">
            <span className="workspace-stat-label">Total</span>
            <strong className="workspace-stat-value">{notes.length}</strong>
          </article>
          <article className="workspace-stat-card">
            <span className="workspace-stat-label">Pinned</span>
            <strong className="workspace-stat-value">{pinnedNotes.length}</strong>
          </article>
          <article className="workspace-stat-card">
            <span className="workspace-stat-label">Recent</span>
            <strong className="workspace-stat-value">{recentNotes.length}</strong>
          </article>
        </div>

        <div className="notes-filters">
          <label className="notes-filter-label">
            Search
            <input
              aria-label="Search"
              className="notes-filter-input"
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <label className="notes-filter-label">
            Subject filter
            <input
              aria-label="Subject filter"
              className="notes-filter-input"
              type="text"
              value={subjectFilter}
              onChange={(event) => setSubjectFilter(event.target.value)}
            />
          </label>
          <label className="notes-filter-label">
            Tag filter
            <input
              aria-label="Tag filter"
              className="notes-filter-input"
              type="text"
              value={tagFilter}
              onChange={(event) => setTagFilter(event.target.value)}
            />
          </label>
          <label className="notes-toggle-filter">
            <input
              aria-label="Show archived"
              type="checkbox"
              checked={showArchived}
              onChange={(event) => {
                setShowArchived(event.target.checked);
              }}
            />
            Show archived
          </label>
        </div>

        {recentNotes.length > 0 ? (
          <section className="notes-section" data-testid="notes-section-recent">
            <h2>
              Recent
              <span>{recentNotes.length}</span>
            </h2>
            <div className="notes-chip-list">
              {recentNotes.map((note) => (
                <button
                  key={`recent-${note.note_id}`}
                  type="button"
                  className={`notes-chip${note.note_id === selectedNoteId ? " selected" : ""}`}
                  onClick={() => setSelectedNoteId(note.note_id)}
                >
                  {note.note_title}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {pinnedNotes.length > 0 ? (
          <section className="notes-section" data-testid="notes-section-pinned">
            <h2>
              Pinned
              <span>{pinnedNotes.length}</span>
            </h2>
            <ul className="notes-list">
              {pinnedNotes.map((note) => (
                <li key={`pinned-${note.note_id}`}>{renderNoteButton(note)}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="notes-section" data-testid="notes-section-all">
          <h2>
            All notes
            <span>{unpinnedNotes.length}</span>
          </h2>
          <ul
            className="notes-list"
            role="listbox"
            aria-label="Notes"
            tabIndex={0}
            onKeyDown={handleListKeyDown}
          >
            {unpinnedNotes.map((note) => (
              <li
                key={note.note_id}
                role="option"
                aria-selected={note.note_id === selectedNoteId}
              >
                {renderNoteButton(note, note.note_id === highlightedNoteId)}
              </li>
            ))}
          </ul>
          {!isLoading && unpinnedNotes.length === 0 ? <p className="notes-empty">No unpinned notes.</p> : null}
        </section>

        {isLoading ? <p className="notes-loading">Loading notes...</p> : null}
        {!isLoading && notes.length === 0 ? <p className="notes-empty">No notes yet. Create your first note.</p> : null}
        {errorMessage ? (
          <div className="notes-error-panel">
            <p className="notes-error">{errorMessage}</p>
            <button type="button" className="notes-retry-button" onClick={() => void refreshNotes(selectedNoteId)}>
              Retry
            </button>
          </div>
        ) : null}
      </aside>

      <main className="notes-editor-panel">
        {selectedNoteId ? (
          <NoteEditor
            key={selectedNoteId}
            noteId={selectedNoteId}
            baseUrl={baseUrl}
            onMetadataSaved={(payload) => {
              void handleMetadataSaved(payload);
            }}
          />
        ) : (
          <div className="notes-empty-state">
            <h2>No note selected</h2>
            <p>Select or create a note to begin editing.</p>
          </div>
        )}
      </main>

      {contextMenu ? (
        <ul
          ref={contextMenuRef}
          className="note-context-menu"
          role="menu"
          aria-label="Note actions"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <li>
            <button type="button" role="menuitem" onClick={() => void handleRenameNote(contextMenu.noteId)}>
              Rename note
            </button>
          </li>
          <li>
            <button type="button" role="menuitem" onClick={() => void handleTogglePinnedNote(contextMenu.noteId)}>
              {contextNote?.is_pinned ? "Unpin note" : "Pin note"}
            </button>
          </li>
          <li>
            <button
              type="button"
              role="menuitem"
              className="danger"
              onClick={() => void handleDeleteNote(contextMenu.noteId)}
            >
              Delete note
            </button>
          </li>
        </ul>
      ) : null}
    </section>
  );
}
