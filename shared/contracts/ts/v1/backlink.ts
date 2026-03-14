export interface BacklinkItem {
  source_note_id: string;
  source_note_title: string;
  matched_title: string;
  snippet: string;
  updated_at: string;
}

export interface BacklinksResponse {
  note_id: string;
  items: BacklinkItem[];
}
