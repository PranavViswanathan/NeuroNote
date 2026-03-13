export interface WorkspaceSelection {
  selectedNoteId: string | null;
  highlightedIndex: number;
}

export interface WorkspaceFilters {
  search: string;
  subjectId: string;
  tag: string;
  showArchived: boolean;
}
