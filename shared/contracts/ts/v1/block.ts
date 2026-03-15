export interface BlockNode {
  block_uid: string;
  note_id: string;
  parent_block_uid: string | null;
  sibling_order: number;
  block_index: number;
  content_text: string;
  rich_content: Record<string, unknown>;
}

export interface ListBlocksResponse {
  items: BlockNode[];
}

export interface BlockSearchItem {
  block_uid: string;
  note_id: string;
  note_title: string;
  content_text: string;
}

export interface BlockSearchResponse {
  items: BlockSearchItem[];
}

export interface BlockBacklinkItem {
  source_block_uid: string;
  source_note_id: string;
  source_note_title: string;
  snippet: string;
  updated_at: string;
}

export interface BlockBacklinksResponse {
  block_uid: string;
  items: BlockBacklinkItem[];
}

