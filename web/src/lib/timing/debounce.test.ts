import { beforeEach, describe, expect, it, vi } from "vitest";

import { createDebouncedAction } from "./debounce";

describe("createDebouncedAction", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("coalesces rapid calls into one invocation", () => {
    const handler = vi.fn();
    const debounced = createDebouncedAction(handler, 100);

    debounced.call();
    debounced.call();
    debounced.call();

    vi.advanceTimersByTime(99);
    expect(handler).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("cancels a pending invocation", () => {
    const handler = vi.fn();
    const debounced = createDebouncedAction(handler, 100);

    debounced.call();
    debounced.cancel();
    vi.advanceTimersByTime(200);

    expect(handler).not.toHaveBeenCalled();
  });

  it("flushes a pending invocation immediately", () => {
    const handler = vi.fn();
    const debounced = createDebouncedAction(handler, 100);

    debounced.call();
    debounced.flush();

    expect(handler).toHaveBeenCalledTimes(1);
  });
});
