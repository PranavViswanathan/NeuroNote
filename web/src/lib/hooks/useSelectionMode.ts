import { useCallback, useState } from "react";

export interface UseSelectionModeState {
  selectionMode: boolean;
  selectedNoteIds: Set<string>;
  bulkDeleteDialogOpen: boolean;
  bulkTagDialogOpen: boolean;
  bulkSubjectDialogOpen: boolean;
}

export interface UseSelectionModeActions {
  toggleSelection: (noteId: string) => void;
  selectAll: (noteIds: string[]) => void;
  clearSelection: () => void;
  setSelectionMode: (on: boolean) => void;
  setBulkDeleteDialogOpen: (open: boolean) => void;
  setBulkTagDialogOpen: (open: boolean) => void;
  setBulkSubjectDialogOpen: (open: boolean) => void;
}

export function useSelectionMode(): UseSelectionModeState & UseSelectionModeActions {
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedNoteIds, setSelectedNoteIds] = useState<Set<string>>(new Set());
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [bulkTagDialogOpen, setBulkTagDialogOpen] = useState(false);
  const [bulkSubjectDialogOpen, setBulkSubjectDialogOpen] = useState(false);

  const toggleSelection = useCallback((noteId: string) => {
    setSelectedNoteIds((prev) => {
      const next = new Set(prev);
      if (next.has(noteId)) {
        next.delete(noteId);
      } else {
        next.add(noteId);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((noteIds: string[]) => {
    setSelectedNoteIds(new Set(noteIds));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedNoteIds(new Set());
    setSelectionMode(false);
  }, []);

  return {
    selectionMode,
    selectedNoteIds,
    bulkDeleteDialogOpen,
    bulkTagDialogOpen,
    bulkSubjectDialogOpen,
    toggleSelection,
    selectAll,
    clearSelection,
    setSelectionMode,
    setBulkDeleteDialogOpen,
    setBulkTagDialogOpen,
    setBulkSubjectDialogOpen,
  };
}
