type ProcessStatus = "queued" | "running" | "completed" | "failed";

interface ProcessPollingOptions {
  fetchStatus: () => Promise<{ status: ProcessStatus }>;
  onStatus: (status: ProcessStatus) => void;
  intervalMs?: number;
}

export interface ProcessPollingController {
  start: () => void;
  stop: () => void;
}

const TERMINAL_STATUSES: ProcessStatus[] = ["completed", "failed"];

export function createProcessPollingController(
  options: ProcessPollingOptions,
): ProcessPollingController {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let isRunning = false;

  const scheduleNext = () => {
    timer = setTimeout(() => {
      void poll();
    }, options.intervalMs ?? 1000);
  };

  const poll = async () => {
    if (!isRunning) {
      return;
    }
    try {
      const result = await options.fetchStatus();
      options.onStatus(result.status);

      if (!isRunning) {
        return;
      }
      if (TERMINAL_STATUSES.includes(result.status)) {
        isRunning = false;
        timer = null;
        return;
      }
      scheduleNext();
    } catch {
      isRunning = false;
      timer = null;
      options.onStatus("failed");
    }

  };

  return {
    start: () => {
      if (isRunning) {
        return;
      }
      isRunning = true;
      void poll();
    },
    stop: () => {
      isRunning = false;
      if (timer !== null) {
        clearTimeout(timer);
        timer = null;
      }
    },
  };
}
