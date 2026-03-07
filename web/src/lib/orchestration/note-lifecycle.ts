import { createDebouncedAction } from "../timing/debounce";

interface NoteLifecycleOptions {
  onAutosave: () => void | Promise<void>;
  onQueueProcessing: () => void | Promise<void>;
  autosaveDebounceMs?: number;
  processDebounceMs?: number;
}

export interface NoteLifecycleController {
  onEdit: () => void;
  onBlur: () => void;
  dispose: () => void;
}

export function createNoteLifecycleController(
  options: NoteLifecycleOptions,
): NoteLifecycleController {
  const autosave = createDebouncedAction(
    () => void options.onAutosave(),
    options.autosaveDebounceMs ?? 800,
  );
  const processQueue = createDebouncedAction(
    () => void options.onQueueProcessing(),
    options.processDebounceMs ?? 3000,
  );

  return {
    onEdit: () => {
      autosave.call();
      processQueue.call();
    },
    onBlur: () => {
      autosave.flush();
      processQueue.flush();
    },
    dispose: () => {
      autosave.cancel();
      processQueue.cancel();
    },
  };
}
