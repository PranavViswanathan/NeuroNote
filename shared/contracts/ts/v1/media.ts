export interface UploadImageRequest {
  note_id: string;
  filename: string;
  mime_type: string;
  content_base64: string;
}

export interface UploadImageResponse {
  asset_id: string;
  note_id: string;
  src: string;
  mime_type: string;
  byte_size: number;
}

export interface DeleteImageResponse {
  asset_id: string;
  deleted: boolean;
}
