export interface NoteConnectionItem {
  related_note_id: string;
  related_note_title: string;
  strength: number;
  via_concepts: string[];
}

export interface NoteConnectionsResponse {
  note_id: string;
  connections: NoteConnectionItem[];
}
