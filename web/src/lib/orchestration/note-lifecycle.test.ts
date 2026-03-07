import { beforeEach, describe, expect, it, vi } from "vitest";

import { createNoteLifecycleController } from "./note-lifecycle";

describe("createNoteLifecycleController", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("debounces autosave and process trigger on rapid edits", () => {
    const onAutosave = vi.fn();
    const onProcess = vi.fn();
    const controller = createNoteLifecycleController({
      onAutosave,
      onQueueProcessing: onProcess,
      autosaveDebounceMs: 800,
      processDebounceMs: 3000,
    });

    controller.onEdit();
    vi.advanceTimersByTime(300);
    controller.onEdit();
    vi.advanceTimersByTime(300);
    controller.onEdit();

    vi.advanceTimersByTime(799);
    expect(onAutosave).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(onAutosave).toHaveBeenCalledTimes(1);
    expect(onProcess).not.toHaveBeenCalled();

    vi.advanceTimersByTime(2199);
    expect(onProcess).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(onProcess).toHaveBeenCalledTimes(1);
  });

  it("flushes save and processing on blur", () => {
    const onAutosave = vi.fn();
    const onProcess = vi.fn();
    const controller = createNoteLifecycleController({
      onAutosave,
      onQueueProcessing: onProcess,
      autosaveDebounceMs: 800,
      processDebounceMs: 3000,
    });

    controller.onEdit();
    controller.onBlur();

    expect(onAutosave).toHaveBeenCalledTimes(1);
    expect(onProcess).toHaveBeenCalledTimes(1);
  });

  it("cancels pending work on dispose", () => {
    const onAutosave = vi.fn();
    const onProcess = vi.fn();
    const controller = createNoteLifecycleController({
      onAutosave,
      onQueueProcessing: onProcess,
      autosaveDebounceMs: 800,
      processDebounceMs: 3000,
    });

    controller.onEdit();
    controller.dispose();
    vi.advanceTimersByTime(5000);

    expect(onAutosave).not.toHaveBeenCalled();
    expect(onProcess).not.toHaveBeenCalled();
  });
});
