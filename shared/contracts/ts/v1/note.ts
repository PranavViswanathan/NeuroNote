export interface SaveNoteRequest {
  note_id: string;
  content_json: Record<string, unknown>;
  content_text: string;
  updated_at: string;
}

export interface SaveNoteResponse {
  note_id: string;
  saved_at: string;
  version: number;
}

export interface GetNoteResponse {
  note_id: string;
  content_json: Record<string, unknown>;
  content_text: string;
  updated_at: string;
  version: number;
}

export interface NoteSummary {
  note_id: string;
  content_text: string;
  updated_at: string;
  version: number;
}

export interface ListNotesResponse {
  items: NoteSummary[];
  total: number;
}
