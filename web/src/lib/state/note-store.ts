export type SaveStatus = "idle" | "saving" | "saved" | "error";

export type ProcessStatus =
  | "idle"
  | "queued"
  | "running"
  | "completed"
  | "failed";

export interface NoteState {
  documentJson: Record<string, unknown>;
  plainText: string;
  dirty: boolean;
  saveStatus: SaveStatus;
  processStatus: ProcessStatus;
}

export function createInitialNoteState(): NoteState {
  return {
    documentJson: {},
    plainText: "",
    dirty: false,
    saveStatus: "idle",
    processStatus: "idle",
  };
}
