import { request } from "./client";
import { API_BASE_URL, API_PREFIX } from "../config";
import type {
  GenerationResponse,
  GenerationRun,
  GenerationRunListItem,
  TimetableResultPayload,
} from "../types/api";

export type GenerationParams = {
  generations?: number;
};

export const generateTimetable = async (
  datasetId?: number,
  params?: GenerationParams
) => {
  const body: Record<string, unknown> = {};
  if (typeof datasetId === "number") {
    body.dataset_id = datasetId;
  }
  if (params && Object.keys(params).length > 0) {
    body.params = params;
  }
  return request<GenerationResponse>("/timetables/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
};

export const getRunStatus = async (runId: number) => {
  return request<GenerationRun>(`/timetables/runs/${runId}`);
};

export const getRunResult = async (runId: number) => {
  return request<TimetableResultPayload>(`/timetables/runs/${runId}/result`);
};

export const listRuns = async () => {
  return request<GenerationRunListItem[]>("/timetables/runs");
};

export const getRunPdfUrl = (runId: number) => {
  return `${API_BASE_URL}${API_PREFIX}/timetables/runs/${runId}/pdf`;
};

export const deleteRunPdf = async (runId: number) => {
  return request<void>(`/timetables/runs/${runId}/pdf`, { method: "DELETE" });
};

export const deleteRun = async (runId: number) => {
  return request<void>(`/timetables/runs/${runId}`, { method: "DELETE" });
};
