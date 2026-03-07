export interface DebouncedAction {
  call: () => void;
  cancel: () => void;
  flush: () => void;
}

export function createDebouncedAction(
  handler: () => void,
  delayMs: number,
): DebouncedAction {
  let timer: ReturnType<typeof setTimeout> | null = null;

  return {
    call: () => {
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(() => {
        timer = null;
        handler();
      }, delayMs);
    },
    cancel: () => {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
    },
    flush: () => {
      if (timer) {
        clearTimeout(timer);
        timer = null;
        handler();
      }
    },
  };
}
