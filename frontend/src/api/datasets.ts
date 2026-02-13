import { ApiError, request } from "./client";
import { API_BASE_URL, API_PREFIX } from "../config";
import type { Dataset, DatasetCreate } from "../types/api";

export const listDatasets = async () => {
  return request<Dataset[]>("/datasets");
};

export const createDataset = async (payload: DatasetCreate) => {
  return request<Dataset>("/datasets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const downloadDatasetExcel = async (datasetId: number) => {
  const response = await fetch(
    `${API_BASE_URL}${API_PREFIX}/datasets/${datasetId}/excel`,
  );

  if (!response.ok) {
    let message = response.statusText || "Request failed";
    try {
      const data = (await response.json()) as { detail?: string; message?: string };
      message = data.detail || data.message || message;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, message);
  }

  return response.blob();
};

export const uploadDatasetExcel = async (name: string, file: File) => {
  const formData = new FormData();
  formData.append("name", name);
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}${API_PREFIX}/datasets/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = response.statusText || "Request failed";
    try {
      const data = (await response.json()) as { detail?: string; message?: string };
      message = data.detail || data.message || message;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as Dataset;
};
