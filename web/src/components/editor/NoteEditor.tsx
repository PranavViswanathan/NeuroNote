"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { EditorToolbar } from "./EditorToolbar";
import { TipTapEditor, type TipTapUpdatePayload } from "./TipTapEditor";
import {
  fetchProcessingStatus,
  getNote,
  queueNoteProcessing,
  saveNote,
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

interface NoteEditorProps {
  noteId: string;
  baseUrl: string;
  autosaveDebounceMs?: number;
  processDebounceMs?: number;
}

interface NoteSnapshot {
  noteTitle: string;
  documentJson: EditorDoc;
  plainText: string;
  updatedAt: string;
}

function makeHash(content: string): string {
  let hash = 0;
  for (let i = 0; i < content.length; i += 1) {
    hash = (hash * 31 + content.charCodeAt(i)) | 0;
  }
  return `h${Math.abs(hash)}`;
}

export function NoteEditor({
  noteId,
  baseUrl,
  autosaveDebounceMs = 800,
  processDebounceMs = 3000,
}: NoteEditorProps) {
  const [documentJson, setDocumentJson] = useState<EditorDoc>(createEmptyEditorDoc());
  const [noteTitle, setNoteTitle] = useState("Untitled");
  const [plainText, setPlainText] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [processStatus, setProcessStatus] = useState<ProcessStatus>("idle");
  const [isLoading, setIsLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState(new Date().toISOString());

  const latestSnapshotRef = useRef<NoteSnapshot>({
    noteTitle: "Untitled",
    documentJson: createEmptyEditorDoc(),
    plainText: "",
    updatedAt,
  });
  const activeJobIdRef = useRef<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof createProcessPollingController> | null>(null);
  const lifecycleRef = useRef<ReturnType<typeof createNoteLifecycleController> | null>(null);

  useEffect(() => {
    latestSnapshotRef.current = { noteTitle, documentJson, plainText, updatedAt };
  }, [noteTitle, documentJson, plainText, updatedAt]);

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
        setNoteTitle(nextTitle);
        setDocumentJson(nextDoc);
        setPlainText(nextText);
        setUpdatedAt(note.updated_at);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setNoteTitle("Untitled");
        setDocumentJson(createEmptyEditorDoc());
        setPlainText("");
        setUpdatedAt(new Date().toISOString());
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
      await saveNote(baseUrl, {
        note_id: noteId,
        note_title: snapshot.noteTitle.trim() || "Untitled",
        content_json: snapshot.documentJson,
        content_text: snapshot.plainText || " ",
        updated_at: snapshot.updatedAt,
      });

      setSaveStatus("saved");
      if (snapshot.updatedAt === latestSnapshotRef.current.updatedAt) {
        setDirty(false);
      }
    } catch {
      setSaveStatus("error");
    }
  }, [baseUrl, noteId]);

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
    lifecycleRef.current?.onEdit();
  }, []);

  const handleTitleChange = useCallback(
    (nextTitle: string) => {
      const nextUpdatedAt = new Date().toISOString();
      setNoteTitle(nextTitle);
      setUpdatedAt(nextUpdatedAt);
      setDirty(true);
      setSaveStatus("idle");
      lifecycleRef.current?.onEdit();
    },
    [],
  );

  return (
    <section data-testid="note-editor">
      <EditorToolbar dirty={dirty} saveStatus={saveStatus} processStatus={processStatus} />
      <label>
        <span className="sr-only">Note title</span>
        <input
          aria-label="Note title"
          type="text"
          value={noteTitle}
          onChange={(event) => handleTitleChange(event.target.value)}
          disabled={isLoading}
        />
      </label>
      <TipTapEditor
        value={documentJson}
        onUpdate={handleEditorUpdate}
        onBlur={() => lifecycleRef.current?.onBlur()}
        disabled={isLoading}
      />
    </section>
  );
}
