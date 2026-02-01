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

export interface GenerationRunListItem {
  id: number;
  status: GenerationStatus;
  created_at: string;
  finished_at?: string | null;
  dataset_id?: number | null;
  dataset_name?: string | null;
  has_pdf: boolean;
}

export interface TimetableResult {
  payload: TimetableResultPayload;
}

export interface ScheduleEntry {
  teacher: string;
  subject: string;
}

export type ScheduleLesson = Record<string, ScheduleEntry | null>;
export type ScheduleDay = Record<string, ScheduleLesson>;
export type ScheduleByDay = Record<string, ScheduleDay>;

export interface TimetableResultPayload {
  schedule: ScheduleByDay;
  fitness_score: number;
  generation: number;
  statistics: {
    total_lessons: number;
    teacher_conflicts: number;
    teacher_gaps: number;
  };
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
