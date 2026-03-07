export type SaveStatus = "idle" | "saving" | "saved" | "error";

export type ProcessStatus =
  | "idle"
  | "queued"
  | "running"
  | "completed"
  | "failed";
