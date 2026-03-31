import type { ProcessStatus, SaveStatus } from "../../lib/state/note-store";
import { SaveStatusBadge, ProcessStatusBadge } from "./StatusBadge";

interface EditorToolbarProps {
  dirty: boolean;
  saveStatus: SaveStatus;
  processStatus: ProcessStatus;
}

export function EditorToolbar({ dirty, saveStatus, processStatus }: EditorToolbarProps) {
  return (
    <div className="editor-toolbar" data-testid="editor-toolbar">
      <div data-testid="save-status">
        <SaveStatusBadge status={saveStatus} />
      </div>
      <div data-testid="process-status">
        <ProcessStatusBadge status={processStatus} />
      </div>
    </div>
  );
}
