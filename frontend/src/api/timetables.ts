import { request } from "./client";
import type { GenerationResponse, GenerationRun } from "../types/api";

export const generateTimetable = async (datasetId?: number) => {
  const body = datasetId ? { dataset_id: datasetId } : {};
  return request<GenerationResponse>("/timetables/generate", {
    method: "POST",
    body,
  });
};

export const getRunStatus = async (runId: number) => {
  return request<GenerationRun>(`/timetables/runs/${runId}`);
};

export const getRunResult = async (runId: number) => {
  return request<unknown>(`/timetables/runs/${runId}/result`);
};
