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
import type {
  DeleteImageResponse,
  UploadImageRequest,
  UploadImageResponse,
} from "../../../shared/contracts/ts/v1/media";
import type { BacklinksResponse } from "../../../shared/contracts/ts/v1/backlink";
import type { BlockSearchResponse } from "../../../shared/contracts/ts/v1/block";
import type { LocalGraphResponse } from "../../../shared/contracts/ts/v1/graph";

export class ApiClientError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown = null) {
    super(`Request failed with status ${status}`);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      detail = null;
    }
    throw new ApiClientError(response.status, detail);
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
    throw new ApiClientError(response.status);
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

export async function uploadNoteImage(
  baseUrl: string,
  noteId: string,
  file: File,
): Promise<UploadImageResponse> {
  const raw = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let index = 0; index < raw.length; index += 1) {
    binary += String.fromCharCode(raw[index] ?? 0);
  }
  const payload: UploadImageRequest = {
    note_id: noteId,
    filename: file.name || "image",
    mime_type: file.type || "application/octet-stream",
    content_base64: btoa(binary),
  };

  const response = await fetch(`${baseUrl}/v1/media/uploads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonResponse<UploadImageResponse>(response);
}

export async function deleteNoteImage(baseUrl: string, assetId: string): Promise<DeleteImageResponse> {
  const response = await fetch(`${baseUrl}/v1/media/${assetId}`, {
    method: "DELETE",
  });
  return parseJsonResponse<DeleteImageResponse>(response);
}

export async function exportNoteMarkdown(baseUrl: string, noteId: string): Promise<Blob> {
  const response = await fetch(`${baseUrl}/v1/notes/${noteId}/export/markdown`);
  if (!response.ok) {
    throw new ApiClientError(response.status);
  }
  return response.blob();
}

export async function fetchNoteBacklinks(
  baseUrl: string,
  noteId: string,
): Promise<BacklinksResponse> {
  const response = await fetch(`${baseUrl}/v1/notes/${noteId}/backlinks`);
  return parseJsonResponse<BacklinksResponse>(response);
}

export async function searchBlocks(
  baseUrl: string,
  query: string,
  options: { note_id?: string; limit?: number } = {},
): Promise<BlockSearchResponse> {
  const params = new URLSearchParams();
  params.set("q", query);
  if (options.note_id) {
    params.set("note_id", options.note_id);
  }
  params.set("limit", String(options.limit ?? 8));
  const response = await fetch(`${baseUrl}/v1/blocks/search?${params.toString()}`);
  return parseJsonResponse<BlockSearchResponse>(response);
}

export interface LocalGraphQuery {
  max_hops?: number;
  limit_nodes?: number;
  min_confidence?: number;
  include_types?: string[];
}

export async function fetchLocalGraph(
  baseUrl: string,
  noteId: string,
  query: LocalGraphQuery = {},
): Promise<LocalGraphResponse> {
  const params = new URLSearchParams();
  if (query.max_hops !== undefined) {
    params.set("max_hops", String(query.max_hops));
  }
  if (query.limit_nodes !== undefined) {
    params.set("limit_nodes", String(query.limit_nodes));
  }
  if (query.min_confidence !== undefined) {
    params.set("min_confidence", String(query.min_confidence));
  }
  if (query.include_types && query.include_types.length > 0) {
    params.set("include_types", query.include_types.join(","));
  }

  const suffix = params.toString();
  const response = await fetch(
    `${baseUrl}/v1/graph/local/${noteId}${suffix ? `?${suffix}` : ""}`,
  );
  return parseJsonResponse<LocalGraphResponse>(response);
}
