import type { NoteSummary } from "../../../../shared/contracts/ts/v1/note";

export type QuickSwitchItemKind = "note" | "action";

export type QuickSwitchActionId =
  | "open_note"
  | "create_note"
  | "toggle_pin_selected"
  | "toggle_archive_selected";

export interface QuickSwitchItem {
  id: string;
  kind: QuickSwitchItemKind;
  title: string;
  subtitle?: string;
  keywords: string[];
  actionId: QuickSwitchActionId;
  noteId?: string;
}

export interface BuildQuickSwitchItemsInput {
  notes: NoteSummary[];
  selectedNoteId: string | null;
}

export interface FilterQuickSwitchItemsInput {
  items: QuickSwitchItem[];
  query: string;
}

function buildNoteItem(note: NoteSummary): QuickSwitchItem {
  return {
    id: `note:${note.note_id}`,
    kind: "note",
    title: note.note_title,
    subtitle: `${note.subject_id}${note.tags.length ? ` • ${note.tags.join(", ")}` : ""}`,
    keywords: [note.note_id, note.subject_id, ...note.tags, note.content_text],
    actionId: "open_note",
    noteId: note.note_id,
  };
}

function buildActionItems(
  selected: NoteSummary | undefined,
): QuickSwitchItem[] {
  const base: QuickSwitchItem[] = [
    {
      id: "action:create_note",
      kind: "action",
      title: "Create note",
      subtitle: "Create a new untitled note",
      keywords: ["new", "create", "note"],
      actionId: "create_note",
    },
  ];

  if (!selected) {
    return base;
  }

  base.push({
    id: "action:toggle_pin_selected",
    kind: "action",
    title: selected.is_pinned ? "Unpin selected note" : "Pin selected note",
    subtitle: selected.note_title,
    keywords: ["pin", "unpin", "selected", "star", selected.note_title],
    actionId: "toggle_pin_selected",
    noteId: selected.note_id,
  });

  base.push({
    id: "action:toggle_archive_selected",
    kind: "action",
    title: selected.is_archived ? "Unarchive selected note" : "Archive selected note",
    subtitle: selected.note_title,
    keywords: ["archive", "unarchive", "selected", selected.note_title],
    actionId: "toggle_archive_selected",
    noteId: selected.note_id,
  });

  return base;
}

export function buildQuickSwitchItems(input: BuildQuickSwitchItemsInput): QuickSwitchItem[] {
  const selected = input.notes.find((item) => item.note_id === input.selectedNoteId);
  const actionItems = buildActionItems(selected);
  const noteItems = input.notes.map(buildNoteItem);
  return [...actionItems, ...noteItems];
}

export function filterQuickSwitchItems(input: FilterQuickSwitchItemsInput): QuickSwitchItem[] {
  const normalizedQuery = input.query.trim().toLowerCase();
  if (!normalizedQuery) {
    return input.items;
  }

  return input.items.filter((item) =>
    [item.title, item.subtitle ?? "", ...item.keywords]
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuery),
  );
}
