import type { ProcessStatus, SaveStatus } from "../../lib/state/note-store";

interface EditorToolbarProps {
  dirty: boolean;
  saveStatus: SaveStatus;
  processStatus: ProcessStatus;
}

export function EditorToolbar({ dirty, saveStatus, processStatus }: EditorToolbarProps) {
  return (
    <div className="editor-toolbar" data-testid="editor-toolbar">
      <span className="editor-toolbar-pill" data-testid="dirty-flag">{dirty ? "dirty" : "clean"}</span>
      <span className="editor-toolbar-pill" data-testid="save-status">{saveStatus}</span>
      <span className="editor-toolbar-pill" data-testid="process-status">{processStatus}</span>
    </div>
  );
}
