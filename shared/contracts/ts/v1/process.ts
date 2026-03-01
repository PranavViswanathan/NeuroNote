export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface ProcessNoteRequest {
  note_id: string;
  content_text: string;
  content_hash: string;
  updated_at: string;
}

export interface ProcessNoteResponse {
  job_id: string;
  status: "queued";
}

export interface ProcessStatusResponse {
  job_id: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  error?: string | null;
}
