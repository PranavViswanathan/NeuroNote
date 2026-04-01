"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { EditorToolbar } from "./EditorToolbar";
import { SubjectPicker } from "./SubjectPicker";
import { TagPicker } from "./TagPicker";
import { TipTapEditor, type TipTapUpdatePayload } from "./TipTapEditor";
import { SkeletonEditor } from "../ui/Skeleton";
import { ErrorMessage } from "../ui/ErrorMessage";
import {
  exportNoteMarkdown,
  listNotes,
  searchBlocks,
  fetchProcessingStatus,
  getNote,
  queueNoteProcessing,
  saveNote,
  uploadNoteImage,
} from "../../lib/api-client";
import {
  coerceEditorDoc,
  createEmptyEditorDoc,
  type EditorDoc,
} from "../../lib/editor/serialize";
import { extractPlainText } from "../../lib/editor/text-extract";
import { createNoteLifecycleController } from "../../lib/orchestration/note-lifecycle";
import { createProcessPollingController } from "../../lib/orchestration/process-polling";
import type { ProcessStatus, SaveStatus } from "../../lib/state/note-store";
import type { BlockRefSuggestion, WikiLinkSuggestion } from "./TipTapEditor";

interface NoteEditorProps {
  noteId: string;
  baseUrl: string;
  autosaveDebounceMs?: number;
  processDebounceMs?: number;
  onMetadataSaved?: (payload: NoteMetadataPayload) => void;
  availableSubjects?: string[];
  availableTags?: string[];
}

interface NoteSnapshot {
  noteTitle: string;
  subjectId: string;
  tags: string[];
  isPinned: boolean;
  isArchived: boolean;
  documentJson: EditorDoc;
  plainText: string;
  updatedAt: string;
}

interface NoteMetadataPayload {
  noteId: string;
  noteTitle: string;
  subjectId: string;
  tags: string[];
  isPinned: boolean;
  isArchived: boolean;
  updatedAt: string;
  version: number;
}

interface PersistedMetadataSnapshot {
  noteTitle: string;
  subjectId: string;
  tags: string[];
  isPinned: boolean;
  isArchived: boolean;
}

function makeHash(content: string): string {
  let hash = 0;
  for (let i = 0; i < content.length; i += 1) {
    hash = (hash * 31 + content.charCodeAt(i)) | 0;
  }
  return `h${Math.abs(hash)}`;
}

function makeGeneratedNoteId(): string {
  return `note-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

function parseTagsInput(value: string): string[] {
  const seen = new Set<string>();
  const tags: string[] = [];
  for (const raw of value.split(",")) {
    const normalized = raw.trim().toLowerCase();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    tags.push(normalized);
  }
  return tags;
}

function formatTags(tags: string[]): string {
  return tags.join(", ");
}

function sameTags(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((tag, index) => tag === right[index]);
}

export function NoteEditor({
  noteId,
  baseUrl,
  autosaveDebounceMs = 800,
  processDebounceMs = 3000,
  onMetadataSaved,
  availableSubjects = [],
  availableTags = [],
}: NoteEditorProps) {
  const [documentJson, setDocumentJson] = useState<EditorDoc>(createEmptyEditorDoc());
  const [noteTitle, setNoteTitle] = useState("Untitled");
  const [subjectId, setSubjectId] = useState("inbox");
  const [tagsInput, setTagsInput] = useState("");
  const [isPinned, setIsPinned] = useState(false);
  const [isArchived, setIsArchived] = useState(false);
  const [plainText, setPlainText] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [processStatus, setProcessStatus] = useState<ProcessStatus>("idle");
  const [editorError, setEditorError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState(new Date().toISOString());

  const latestSnapshotRef = useRef<NoteSnapshot>({
    noteTitle: "Untitled",
    subjectId: "inbox",
    tags: [],
    isPinned: false,
    isArchived: false,
    documentJson: createEmptyEditorDoc(),
    plainText: "",
    updatedAt,
  });
  const activeJobIdRef = useRef<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof createProcessPollingController> | null>(null);
  const lifecycleRef = useRef<ReturnType<typeof createNoteLifecycleController> | null>(null);
  const persistedMetadataRef = useRef<PersistedMetadataSnapshot>({
    noteTitle: "Untitled",
    subjectId: "inbox",
    tags: [],
    isPinned: false,
    isArchived: false,
  });

  useEffect(() => {
    latestSnapshotRef.current = {
      noteTitle,
      subjectId: subjectId.trim() || "inbox",
      tags: parseTagsInput(tagsInput),
      isPinned,
      isArchived,
      documentJson,
      plainText,
      updatedAt,
    };
  }, [noteTitle, subjectId, tagsInput, isPinned, isArchived, documentJson, plainText, updatedAt]);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    void getNote(baseUrl, noteId)
      .then((note) => {
        if (!isMounted) {
          return;
        }

        const nextDoc = coerceEditorDoc(note.content_json);
        const nextText = note.content_text || extractPlainText(nextDoc);
        const nextTitle = note.note_title || "Untitled";
        const nextSubject = note.subject_id || "inbox";
        const nextTags = note.tags || [];
        setNoteTitle(nextTitle);
        setSubjectId(nextSubject);
        setTagsInput(formatTags(nextTags));
        setIsPinned(note.is_pinned);
        setIsArchived(note.is_archived);
        setDocumentJson(nextDoc);
        setPlainText(nextText);
        setUpdatedAt(note.updated_at);
        persistedMetadataRef.current = {
          noteTitle: nextTitle,
          subjectId: nextSubject,
          tags: nextTags,
          isPinned: note.is_pinned,
          isArchived: note.is_archived,
        };
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setNoteTitle("Untitled");
        setSubjectId("inbox");
        setTagsInput("");
        setIsPinned(false);
        setIsArchived(false);
        setDocumentJson(createEmptyEditorDoc());
        setPlainText("");
        setUpdatedAt(new Date().toISOString());
        persistedMetadataRef.current = {
          noteTitle: "Untitled",
          subjectId: "inbox",
          tags: [],
          isPinned: false,
          isArchived: false,
        };
      })
      .finally(() => {
        if (isMounted) {
          setSaveStatus("idle");
          setProcessStatus("idle");
          setDirty(false);
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [baseUrl, noteId]);

  const performAutosave = useCallback(async () => {
    const snapshot = latestSnapshotRef.current;
    setSaveStatus("saving");

    try {
      const saveResult = await saveNote(baseUrl, {
        note_id: noteId,
        note_title: snapshot.noteTitle.trim() || "Untitled",
        subject_id: snapshot.subjectId || "inbox",
        tags: snapshot.tags,
        is_pinned: snapshot.isPinned,
        is_archived: snapshot.isArchived,
        content_json: snapshot.documentJson,
        content_text: snapshot.plainText || " ",
        updated_at: snapshot.updatedAt,
      });

      setSaveStatus("saved");
      const nextPersistedMetadata: PersistedMetadataSnapshot = {
        noteTitle: snapshot.noteTitle.trim() || "Untitled",
        subjectId: snapshot.subjectId || "inbox",
        tags: snapshot.tags,
        isPinned: snapshot.isPinned,
        isArchived: snapshot.isArchived,
      };
      const previousPersistedMetadata = persistedMetadataRef.current;
      const metadataChanged =
        previousPersistedMetadata.noteTitle !== nextPersistedMetadata.noteTitle
        || previousPersistedMetadata.subjectId !== nextPersistedMetadata.subjectId
        || previousPersistedMetadata.isPinned !== nextPersistedMetadata.isPinned
        || previousPersistedMetadata.isArchived !== nextPersistedMetadata.isArchived
        || !sameTags(previousPersistedMetadata.tags, nextPersistedMetadata.tags);

      persistedMetadataRef.current = nextPersistedMetadata;
      if (metadataChanged && onMetadataSaved) {
        onMetadataSaved({
          noteId,
          noteTitle: nextPersistedMetadata.noteTitle,
          subjectId: nextPersistedMetadata.subjectId,
          tags: nextPersistedMetadata.tags,
          isPinned: nextPersistedMetadata.isPinned,
          isArchived: nextPersistedMetadata.isArchived,
          updatedAt: snapshot.updatedAt,
          version: saveResult.version,
        });
      }
      if (snapshot.updatedAt === latestSnapshotRef.current.updatedAt) {
        setDirty(false);
      }
    } catch {
      setSaveStatus("error");
    }
  }, [baseUrl, noteId, onMetadataSaved]);

  const startProcessing = useCallback(async () => {
    const snapshot = latestSnapshotRef.current;
    if (snapshot.plainText.trim().length === 0) {
      setProcessStatus("idle");
      return;
    }

    try {
      setProcessStatus("queued");
      const combinedText = `${snapshot.noteTitle.trim()}\n\n${snapshot.plainText}`.trim();
      const queued = await queueNoteProcessing(baseUrl, {
        note_id: noteId,
        content_text: combinedText,
        content_hash: makeHash(combinedText),
        updated_at: snapshot.updatedAt,
      });
      setProcessStatus(queued.status);
      activeJobIdRef.current = queued.job_id;

      pollingRef.current?.stop();
      pollingRef.current = createProcessPollingController({
        fetchStatus: async () => {
          const jobId = activeJobIdRef.current;
          if (!jobId) {
            return { status: "failed" as const };
          }
          const result = await fetchProcessingStatus(baseUrl, jobId);
          return { status: result.status };
        },
        onStatus: (status) => {
          setProcessStatus(status);
        },
      });
      pollingRef.current.start();
    } catch {
      setProcessStatus("failed");
    }
  }, [baseUrl, noteId]);

  useEffect(() => {
    const controller = createNoteLifecycleController({
      onAutosave: () => void performAutosave(),
      onQueueProcessing: () => void startProcessing(),
      autosaveDebounceMs,
      processDebounceMs,
    });
    lifecycleRef.current = controller;

    return () => {
      controller.dispose();
    };
  }, [autosaveDebounceMs, performAutosave, processDebounceMs, startProcessing]);

  useEffect(() => {
    return () => {
      pollingRef.current?.stop();
    };
  }, []);

  const handleEditorUpdate = useCallback((payload: TipTapUpdatePayload) => {
    const nextDoc = coerceEditorDoc(payload.json);
    const nextText = payload.text;
    const nextUpdatedAt = new Date().toISOString();

    setDocumentJson(nextDoc);
    setPlainText(nextText);
    setUpdatedAt(nextUpdatedAt);
    setDirty(true);
    setSaveStatus("idle");
    setEditorError(null);
    lifecycleRef.current?.onEdit();
  }, []);

  const handleTitleChange = useCallback(
    (nextTitle: string) => {
      const nextUpdatedAt = new Date().toISOString();
      setNoteTitle(nextTitle);
      setUpdatedAt(nextUpdatedAt);
      setDirty(true);
      setSaveStatus("idle");
      setEditorError(null);
      lifecycleRef.current?.onEdit();
    },
    [],
  );

  const handleSubjectChange = useCallback((nextSubjectId: string) => {
    const nextUpdatedAt = new Date().toISOString();
    setSubjectId(nextSubjectId);
    setUpdatedAt(nextUpdatedAt);
    setDirty(true);
    setSaveStatus("idle");
    setEditorError(null);
    lifecycleRef.current?.onEdit();
  }, []);

  const handleTagsChange = useCallback((nextTagsInput: string) => {
    const nextUpdatedAt = new Date().toISOString();
    setTagsInput(nextTagsInput);
    setUpdatedAt(nextUpdatedAt);
    setDirty(true);
    setSaveStatus("idle");
    setEditorError(null);
    lifecycleRef.current?.onEdit();
  }, []);

  const handlePinnedChange = useCallback((nextPinned: boolean) => {
    const nextUpdatedAt = new Date().toISOString();
    setIsPinned(nextPinned);
    setUpdatedAt(nextUpdatedAt);
    setDirty(true);
    setSaveStatus("idle");
    setEditorError(null);
    lifecycleRef.current?.onEdit();
  }, []);

  const handleArchivedChange = useCallback((nextArchived: boolean) => {
    const nextUpdatedAt = new Date().toISOString();
    setIsArchived(nextArchived);
    setUpdatedAt(nextUpdatedAt);
    setDirty(true);
    setSaveStatus("idle");
    setEditorError(null);
    lifecycleRef.current?.onEdit();
  }, []);

  const searchWikiLinks = useCallback(
    async (query: string): Promise<WikiLinkSuggestion[]> => {
      const response = await listNotes(baseUrl, {
        limit: 8,
        offset: 0,
        search: query.trim() || undefined,
        is_archived: false,
      });
      return response.items.map((item) => ({
        noteId: item.note_id,
        title: item.note_title,
      }));
    },
    [baseUrl],
  );

  const createWikiLinkNote = useCallback(
    async (title: string): Promise<WikiLinkSuggestion> => {
      const nextTitle = title.trim() || "Untitled";
      const noteId = makeGeneratedNoteId();
      await saveNote(baseUrl, {
        note_id: noteId,
        note_title: nextTitle,
        subject_id: "inbox",
        tags: [],
        is_pinned: false,
        is_archived: false,
        content_json: createEmptyEditorDoc(),
        content_text: " ",
        updated_at: new Date().toISOString(),
      });
      return {
        noteId,
        title: nextTitle,
      };
    },
    [baseUrl],
  );

  const searchBlockRefTargets = useCallback(
    async (query: string): Promise<BlockRefSuggestion[]> => {
      const response = await searchBlocks(baseUrl, query, { limit: 8 });
      return response.items.map((item) => ({
        blockUid: item.block_uid,
        noteId: item.note_id,
        noteTitle: item.note_title,
        contentText: item.content_text,
      }));
    },
    [baseUrl],
  );

  const handleUploadImage = useCallback(
    async (file: File) => {
      const uploaded = await uploadNoteImage(baseUrl, noteId, file);
      return {
        assetId: uploaded.asset_id,
        src: `${baseUrl}${uploaded.src}`,
        mimeType: uploaded.mime_type,
      };
    },
    [baseUrl, noteId],
  );

  const handleExportMarkdown = useCallback(async () => {
    try {
      const archive = await exportNoteMarkdown(baseUrl, noteId);
      const url = URL.createObjectURL(archive);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${noteId}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
      setEditorError(null);
    } catch {
      setEditorError("Failed to export markdown");
    }
  }, [baseUrl, noteId]);

  if (isLoading) {
    return <SkeletonEditor />;
  }

  return (
    <section className="note-editor" data-testid="note-editor">
      <EditorToolbar dirty={dirty} saveStatus={saveStatus} processStatus={processStatus} />
      <label className="note-editor-field">
        <span className="sr-only">Note title</span>
        <input
          className="note-editor-input note-editor-title"
          aria-label="Note title"
          type="text"
          value={noteTitle}
          onChange={(event) => handleTitleChange(event.target.value)}
          disabled={isLoading}
        />
      </label>
      <div className="note-editor-meta-grid">
        <div className="note-editor-field">
          <span className="sr-only">Subject</span>
          <SubjectPicker
            value={subjectId}
            onChange={handleSubjectChange}
            suggestions={availableSubjects}
            disabled={isLoading}
          />
        </div>
        <div className="note-editor-field">
          <span className="sr-only">Tags</span>
          <TagPicker
            value={parseTagsInput(tagsInput)}
            onChange={(tags) => handleTagsChange(tags.join(", "))}
            suggestions={availableTags}
            disabled={isLoading}
          />
        </div>
      </div>
      <div className="note-editor-toggle-row">
        <label className="note-editor-toggle">
          <input
            aria-label="Pinned"
            type="checkbox"
            checked={isPinned}
            onChange={(event) => handlePinnedChange(event.target.checked)}
            disabled={isLoading}
          />
          Pinned
        </label>
        <label className="note-editor-toggle">
          <input
            aria-label="Archived"
            type="checkbox"
            checked={isArchived}
            onChange={(event) => handleArchivedChange(event.target.checked)}
            disabled={isLoading}
          />
          Archived
        </label>
      </div>
      <div className="note-editor-toggle-row">
        <button
          type="button"
          className="editor-command-button"
          onClick={() => {
            void handleExportMarkdown();
          }}
          disabled={isLoading}
          aria-label="Export markdown"
        >
          Export Markdown
        </button>
      </div>
      <TipTapEditor
        value={documentJson}
        onUpdate={handleEditorUpdate}
        onBlur={() => lifecycleRef.current?.onBlur()}
        disabled={isLoading}
        onUploadImage={handleUploadImage}
        onSearchWikiLinks={searchWikiLinks}
        onCreateWikiLink={createWikiLinkNote}
        onSearchBlockRefs={searchBlockRefTargets}
        onEditorError={(message) => setEditorError(message)}
      />
      {editorError ? <ErrorMessage message={editorError} compact /> : null}
    </section>
  );
}
