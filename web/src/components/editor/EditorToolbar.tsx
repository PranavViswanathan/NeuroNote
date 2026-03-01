import type { ProcessStatus, SaveStatus } from "../../lib/state/note-store";

interface EditorToolbarProps {
  dirty: boolean;
  saveStatus: SaveStatus;
  processStatus: ProcessStatus;
}

export function EditorToolbar({ dirty, saveStatus, processStatus }: EditorToolbarProps) {
  return (
    <div data-testid="editor-toolbar">
      <span data-testid="dirty-flag">{dirty ? "dirty" : "clean"}</span>
      <span data-testid="save-status">{saveStatus}</span>
      <span data-testid="process-status">{processStatus}</span>
    </div>
  );
}
