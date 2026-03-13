import type {
  GetNoteResponse,
  ListNotesResponse,
  SaveNoteRequest,
  SaveNoteResponse,
} from "../../../shared/contracts/ts/v1/note";
import type {
  ProcessNoteRequest,
  ProcessNoteResponse,
  ProcessStatusResponse,
} from "../../../shared/contracts/ts/v1/process";

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function saveNote(
  baseUrl: string,
  payload: SaveNoteRequest,
): Promise<SaveNoteResponse> {
  const response = await fetch(`${baseUrl}/v1/notes/${payload.note_id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse<SaveNoteResponse>(response);
}

export async function getNote(baseUrl: string, noteId: string): Promise<GetNoteResponse> {
  const response = await fetch(`${baseUrl}/v1/notes/${noteId}`);
  return parseJsonResponse<GetNoteResponse>(response);
}

export interface ListNotesQuery {
  limit?: number;
  offset?: number;
  search?: string;
  subject_id?: string;
  tag?: string;
  is_archived?: boolean;
  is_pinned?: boolean;
}

export async function listNotes(
  baseUrl: string,
  query: ListNotesQuery = {},
): Promise<ListNotesResponse> {
  const params = new URLSearchParams();
  if (query.limit !== undefined) {
    params.set("limit", String(query.limit));
  }
  if (query.offset !== undefined) {
    params.set("offset", String(query.offset));
  }
  if (query.search) {
    params.set("search", query.search);
  }
  if (query.subject_id) {
    params.set("subject_id", query.subject_id);
  }
  if (query.tag) {
    params.set("tag", query.tag);
  }
  if (query.is_archived !== undefined) {
    params.set("is_archived", String(query.is_archived));
  }
  if (query.is_pinned !== undefined) {
    params.set("is_pinned", String(query.is_pinned));
  }

  const suffix = params.toString();
  const response = await fetch(`${baseUrl}/v1/notes${suffix ? `?${suffix}` : ""}`);
  return parseJsonResponse<ListNotesResponse>(response);
}

export async function deleteNote(baseUrl: string, noteId: string): Promise<void> {
  const response = await fetch(`${baseUrl}/v1/notes/${noteId}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
}

export async function queueNoteProcessing(
  baseUrl: string,
  payload: ProcessNoteRequest,
): Promise<ProcessNoteResponse> {
  const response = await fetch(`${baseUrl}/v1/process-note`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse<ProcessNoteResponse>(response);
}

export async function fetchProcessingStatus(
  baseUrl: string,
  jobId: string,
): Promise<ProcessStatusResponse> {
  const response = await fetch(`${baseUrl}/v1/process-status/${jobId}`);
  return parseJsonResponse<ProcessStatusResponse>(response);
}
