import { useCallback, useRef, useState } from "react";
import { fetchNoteBacklinks } from "../api-client";
import type { BacklinkItem } from "../../../../shared/contracts/ts/v1/backlink";

export interface UseBacklinksState {
  isOpen: boolean;
  items: BacklinkItem[];
  isLoading: boolean;
  errorMessage: string | null;
}

export interface UseBacklinksActions {
  open: (noteId: string) => void;
  close: () => void;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
}

export function useBacklinks(baseUrl: string): UseBacklinksState & UseBacklinksActions {
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<BacklinkItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const requestTokenRef = useRef(0);

  const load = useCallback(
    async (noteId: string) => {
      const token = requestTokenRef.current + 1;
      requestTokenRef.current = token;
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const response = await fetchNoteBacklinks(baseUrl, noteId);
        if (requestTokenRef.current !== token) return;
        setItems(response.items);
      } catch {
        if (requestTokenRef.current !== token) return;
        setItems([]);
        setErrorMessage("Failed to load linked mentions");
      } finally {
        if (requestTokenRef.current === token) {
          setIsLoading(false);
        }
      }
    },
    [baseUrl],
  );

  const close = useCallback(() => {
    setIsOpen(false);
    setIsLoading(false);
    setErrorMessage(null);
    requestTokenRef.current += 1;
    window.setTimeout(() => {
      triggerRef.current?.focus();
    }, 0);
  }, []);

  const open = useCallback(
    (noteId: string) => {
      setIsOpen(true);
      setItems([]);
      void load(noteId);
    },
    [load],
  );

  return { isOpen, items, isLoading, errorMessage, open, close, triggerRef };
}
