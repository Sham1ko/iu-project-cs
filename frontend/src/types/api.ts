export type GenerationStatus = "queued" | "running" | "done" | "failed";

export interface GenerationResponse {
  run_id: number;
  status: GenerationStatus;
}

export interface GenerationRun {
  id: number;
  status: GenerationStatus;
  progress: number;
  params?: Record<string, unknown> | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  dataset_id?: number | null;
}

export interface TimetableResult {
  payload: unknown;
}

export interface Dataset {
  id: number;
  name: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface DatasetCreate {
  name: string;
  payload: Record<string, unknown>;
}
