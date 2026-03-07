import type {
  GetNoteResponse,
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
