/** Generate a unique note ID in the format `note-{timestamp}-{random}`. */
export function makeNewNoteId(): string {
  return `note-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}
