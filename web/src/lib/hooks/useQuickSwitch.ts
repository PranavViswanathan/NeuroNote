import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildQuickSwitchItems,
  filterQuickSwitchItems,
  type QuickSwitchItem,
} from "../workspace/quick-switch";
import type { NoteSummary } from "../../../../shared/contracts/ts/v1/note";

function clampIndex(index: number, size: number): number {
  if (size <= 0) return 0;
  if (index < 0) return size - 1;
  if (index >= size) return 0;
  return index;
}

export interface UseQuickSwitchState {
  isOpen: boolean;
  query: string;
  selectedIndex: number;
  items: QuickSwitchItem[];
  filteredItems: QuickSwitchItem[];
}

export interface UseQuickSwitchActions {
  open: () => void;
  close: () => void;
  setQuery: (query: string) => void;
  setSelectedIndex: (index: number) => void;
  moveSelection: (delta: number) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

export function useQuickSwitch(
  notes: NoteSummary[],
  selectedNoteId: string | null,
): UseQuickSwitchState & UseQuickSwitchActions {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const items = useMemo(
    () => buildQuickSwitchItems({ notes, selectedNoteId }),
    [notes, selectedNoteId],
  );

  const filteredItems = useMemo(
    () => filterQuickSwitchItems({ items, query }),
    [items, query],
  );

  // Auto-focus input when opened
  useEffect(() => {
    if (!isOpen) return;
    inputRef.current?.focus();
  }, [isOpen]);

  // Clamp index when filtered list changes size
  useEffect(() => {
    setSelectedIndex((current) => clampIndex(current, filteredItems.length));
  }, [filteredItems.length]);

  const open = useCallback(() => {
    setIsOpen(true);
    setQuery("");
    setSelectedIndex(0);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setQuery("");
    setSelectedIndex(0);
  }, []);

  const moveSelection = useCallback(
    (delta: number) => {
      setSelectedIndex((current) => clampIndex(current + delta, filteredItems.length));
    },
    [filteredItems.length],
  );

  return {
    isOpen,
    query,
    selectedIndex,
    items,
    filteredItems,
    open,
    close,
    setQuery,
    setSelectedIndex,
    moveSelection,
    inputRef,
  };
}
