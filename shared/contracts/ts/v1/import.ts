export interface ImportNoteRequest {
  filename: string;
  content: string;
  subject_id?: string;
}

export interface ImportNoteResponse {
  note_id: string;
  note_title: string;
  saved_at: string;
}
