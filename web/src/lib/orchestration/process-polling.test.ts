import { beforeEach, describe, expect, it, vi } from "vitest";

import { createProcessPollingController } from "./process-polling";

describe("createProcessPollingController", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("polls until it receives a terminal status", async () => {
    const fetchStatus = vi
      .fn()
      .mockResolvedValueOnce({ status: "running" })
      .mockResolvedValueOnce({ status: "completed" });
    const onStatus = vi.fn();

    const controller = createProcessPollingController({
      fetchStatus,
      onStatus,
      intervalMs: 500,
    });

    controller.start();
    await vi.runOnlyPendingTimersAsync();
    await vi.runOnlyPendingTimersAsync();

    expect(fetchStatus).toHaveBeenCalledTimes(2);
    expect(onStatus).toHaveBeenCalledWith("running");
    expect(onStatus).toHaveBeenCalledWith("completed");
  });

  it("stops polling when requested", async () => {
    const fetchStatus = vi.fn().mockResolvedValue({ status: "running" });
    const onStatus = vi.fn();
    const controller = createProcessPollingController({
      fetchStatus,
      onStatus,
      intervalMs: 500,
    });

    controller.start();
    await Promise.resolve();
    controller.stop();
    await vi.advanceTimersByTimeAsync(2000);

    expect(fetchStatus).toHaveBeenCalledTimes(1);
  });
});
